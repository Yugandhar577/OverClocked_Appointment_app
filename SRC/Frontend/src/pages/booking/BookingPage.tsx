import { CalendarDays, Clock, MapPin } from "lucide-react"
import { useEffect, useMemo, useState, type FormEvent } from "react"
import { DayPicker } from "react-day-picker"
import { Link, useLocation, useNavigate, useParams } from "react-router-dom"

import { getAppointmentType, getAppointmentTypeByShare } from "../../api/appointmentTypes"
import { googleCalendarConnect, joinWaitlist } from "../../api/advanced"
import { availability, createBooking } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { AppointmentTypeDetail, AvailabilitySlot } from "../../api/types"
import { useAuth } from "../../auth/useAuth"
import { Button } from "../../components/ui/Button"
import { Field, Select, Textarea } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"
import { formatTime, todayIsoDate } from "../../lib/format"
import { loadFeatureFlags } from "../../lib/featureFlags"
import "react-day-picker/dist/style.css"

function addDaysIso(baseIso: string, days: number) {
  const value = new Date(`${baseIso}T00:00:00`)
  value.setDate(value.getDate() + days)
  return value.toISOString().slice(0, 10)
}

function parseIsoDate(value: string) {
  const [year, month, day] = value.split("-").map(Number)
  return new Date(year, (month ?? 1) - 1, day ?? 1)
}

function toIsoDate(value: Date) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, "0")
  const day = String(value.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

export function BookingPage({ share = false }: { share?: boolean }) {
  const params = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const auth = useAuth()
  const [detail, setDetail] = useState<AppointmentTypeDetail | null>(null)
  const [date, setDate] = useState(todayIsoDate())
  const [resourceId, setResourceId] = useState<string>("")
  const [slots, setSlots] = useState<AvailabilitySlot[]>([])
  const [slotId, setSlotId] = useState("")
  const [people, setPeople] = useState(1)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [error, setError] = useState("")
  const [slotHint, setSlotHint] = useState("")
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [saving, setSaving] = useState(false)
  const [waitlistEnabled, setWaitlistEnabled] = useState(false)
  const [waitlistMessage, setWaitlistMessage] = useState("")

  const appointmentTypeId = share ? undefined : params.appointmentTypeId
  const shareToken = share ? params.shareToken : undefined

  useEffect(() => {
    loadFeatureFlags().then((flags) => setWaitlistEnabled(Boolean(flags.ENABLE_WAITLIST)))
  }, [])

  useEffect(() => {
    const load = shareToken ? getAppointmentTypeByShare(shareToken) : appointmentTypeId ? getAppointmentType(appointmentTypeId) : null
    if (!load) return
    load
      .then((data) => {
        setDetail(data)
        setResourceId(data.resources[0]?.id ?? "")
      })
      .catch((err) => setError(errorMessage(err)))
  }, [appointmentTypeId, shareToken])

  useEffect(() => {
    if (!detail) return
    let cancelled = false
    setLoadingSlots(true)
    setSlotHint("")
    availability({
      appointment_type_id: detail.id,
      resource_id: resourceId || undefined,
      date,
      tz_offset_minutes: -new Date().getTimezoneOffset(),
    })
      .then((data) => {
        if (cancelled) return
        setSlots(data)
        setSlotId(data[0]?.slot_id ?? "")
        if (data.length === 0 && date === todayIsoDate()) {
          setSlotHint("Searching the next available day...")
          return findNextAvailableDate(detail.id, resourceId || undefined, date).then((next) => {
            if (cancelled || !next) {
              setSlotHint("No slots found in the next two weeks.")
              return
            }
            setDate(next.date)
            setSlots(next.slots)
            setSlotId(next.slots[0]?.slot_id ?? "")
            setSlotHint(`Showing next available date: ${next.date}`)
          })
        }
        if (data.length === 0) setSlotHint("Try another date.")
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => {
        if (!cancelled) setLoadingSlots(false)
      })
    return () => {
      cancelled = true
    }
  }, [date, detail, resourceId])

  const selectedSlot = useMemo(() => slots.find((slot) => slot.slot_id === slotId), [slotId, slots])
  const maxPeople = Math.max(1, selectedSlot?.remaining_capacity ?? 1)
  const missingRequired = useMemo(
    () => detail?.questions.some((question) => question.is_mandatory && !String(answers[question.id] ?? "").trim()) ?? false,
    [answers, detail],
  )

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!detail || !slotId) return
    if (!auth.user) {
      navigate("/login", { state: { from: location.pathname } })
      return
    }
    if (missingRequired) {
      setError("Please answer every required question.")
      return
    }
    setSaving(true)
    setError("")
    try {
      const response = await createBooking({
        appointment_type_id: detail.id,
        slot_id: slotId,
        resource_id: resourceId || undefined,
        people_count: people,
        customer_info: {
          full_name: auth.user.full_name,
          email: auth.user.email,
          phone: auth.user.phone ?? undefined,
        },
        answers: detail.questions.map((question) => ({
          question_id: question.id,
          value: answers[question.id] ?? "",
        })),
      })
      if (response.payment_required) {
        navigate(`/booking/${response.booking_id}/pay`, {
          state: {
            summary: {
              title: detail.title,
              price: detail.price ?? null,
              currency: detail.currency,
              isPaid: detail.is_paid,
            },
          },
        })
      } else {
        navigate(`/booking/${response.booking_id}/confirmation`)
      }
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleJoinWaitlist() {
    if (!detail) return
    if (!auth.user) {
      navigate("/login", { state: { from: location.pathname } })
      return
    }
    setError("")
    setWaitlistMessage("")
    try {
      await joinWaitlist({
        appointment_type_id: detail.id,
        slot_id: slotId || undefined,
        notes: `Requested date ${date}`,
      })
      setWaitlistMessage("You have joined the waitlist for this appointment.")
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function openGoogleCalendar() {
    const response = await googleCalendarConnect()
    window.open(response.auth_url, "_blank", "noopener,noreferrer")
  }

  function slotClass(slot: AvailabilitySlot, selected: boolean) {
    if (selected) return "border-ink bg-ink text-paper shadow-sm"
    if (slot.status === "full" || slot.remaining_capacity <= 0) return "border-red-200 bg-red-50 text-red-800"
    if (slot.status === "waitlist" || slot.is_waitlist_reserved) return "border-amber-200 bg-amber-50 text-amber-900"
    return "border-green-200 bg-green-50 text-green-900 hover:border-green-500"
  }

  if (!detail && !error) return <Notice>Loading appointment type...</Notice>

  return (
    <form className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]" onSubmit={submit}>
      <section className="grid gap-5">
        {error && <Notice tone="error">{error}</Notice>}
        {waitlistMessage && <Notice tone="success">{waitlistMessage}</Notice>}
        {detail && (
          <>
            <div className="border-b border-line pb-5">
              <h1 className="text-3xl font-bold text-ink">{detail.title}</h1>
              <div className="mt-3 flex flex-wrap gap-3 text-sm text-neutral-700">
                <span className="flex items-center gap-1">
                  <Clock size={16} />
                  {detail.duration_minutes} minutes
                </span>
                {detail.venue && (
                  <span className="flex items-center gap-1">
                    <MapPin size={16} />
                    {detail.venue}
                  </span>
                )}
              </div>
            </div>
            {!auth.user && (
              <Notice>
                <Link className="font-semibold text-signal" to="/login" state={{ from: location.pathname }}>
                  Sign in
                </Link>{" "}
                before confirming this appointment.
              </Notice>
            )}
            <div className="grid gap-4 rounded-md border border-line bg-paper p-4">
              {detail.resources.length > 0 ? (
                <Field label="Resource">
                  <Select value={resourceId} onChange={(event) => setResourceId(event.target.value)}>
                    {detail.resources.map((resource) => (
                      <option key={resource.id} value={resource.id}>
                        {resource.name} - capacity {resource.capacity}
                      </option>
                    ))}
                  </Select>
                </Field>
              ) : (
                <Notice tone="error">No active resource is attached to this appointment type.</Notice>
              )}
              <div className="grid gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <label className="text-sm font-semibold text-ink">Select a date</label>
                  <Button type="button" variant="secondary" onClick={openGoogleCalendar}>
                    Google Calendar
                  </Button>
                </div>
                <div className="rounded-md border border-line bg-white p-3">
                  <DayPicker
                    mode="single"
                    selected={parseIsoDate(date)}
                    month={parseIsoDate(date)}
                    onSelect={(selected) => {
                      if (!selected) return
                      setDate(toIsoDate(selected))
                    }}
                    disabled={{ before: parseIsoDate(todayIsoDate()) }}
                    showOutsideDays
                  />
                </div>
                <p className="text-xs text-neutral-600">Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</p>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-semibold text-ink">Slots</label>
                {slotHint && <p className="text-sm text-neutral-700">{slotHint}</p>}
                <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                  {slots.map((slot) => (
                    <button
                      key={slot.slot_id}
                      type="button"
                      disabled={slot.remaining_capacity <= 0}
                      onClick={() => {
                        if (slot.remaining_capacity <= 0) return
                        setSlotId(slot.slot_id)
                        setPeople(1)
                      }}
                      className={`focus-ring rounded-md border px-3 py-2 text-sm font-semibold transition disabled:cursor-not-allowed ${slotClass(slot, slotId === slot.slot_id)}`}
                    >
                      {formatTime(slot.start_datetime)}
                      <span className="block text-xs opacity-80">
                        {slot.status === "full" || slot.remaining_capacity <= 0
                          ? "Fully booked"
                          : slot.status === "waitlist" || slot.is_waitlist_reserved
                            ? "Waitlist reserved"
                            : `${slot.remaining_capacity} left`}
                      </span>
                    </button>
                  ))}
                </div>
                {loadingSlots && <Notice>Loading slots...</Notice>}
                {!loadingSlots && slots.length === 0 && <Notice>No slots available for this date.</Notice>}
                {!loadingSlots && slots.length === 0 && waitlistEnabled && (
                  <Button type="button" variant="secondary" onClick={handleJoinWaitlist}>
                    Join waitlist
                  </Button>
                )}
              </div>
              {detail.manage_capacity && (
                <Field label="Party size">
                  <Select value={people} onChange={(event) => setPeople(Number(event.target.value))}>
                    {Array.from({ length: maxPeople }, (_, index) => index + 1).map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </Select>
                </Field>
              )}
              {detail.questions.map((question) => (
                <Field key={question.id} label={`${question.question_text}${question.is_mandatory ? " *" : ""}`}>
                  {question.answer_type === "boolean" ? (
                    <Select value={answers[question.id] ?? ""} onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })}>
                      <option value="">Select</option>
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </Select>
                  ) : (
                    <Textarea value={answers[question.id] ?? ""} onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })} />
                  )}
                </Field>
              ))}
            </div>
          </>
        )}
      </section>
      <aside className="h-fit rounded-md border border-line bg-paper p-4 shadow-panel">
        <h2 className="text-lg font-bold text-ink">Summary</h2>
        <dl className="mt-4 grid gap-3 text-sm">
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">Date</dt>
            <dd className="font-semibold">{date}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">Time</dt>
            <dd className="font-semibold">{selectedSlot ? formatTime(selectedSlot.start_datetime) : "-"}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">People</dt>
            <dd className="font-semibold">{people}</dd>
          </div>
        </dl>
        {selectedSlot && (
          <div className="mt-4 rounded-md border border-line bg-white p-3 text-sm text-neutral-700">
            <div className="font-semibold text-ink">{selectedSlot.remaining_capacity} seats remaining</div>
            <div>{detail?.requires_confirmation ? "Organiser confirmation required" : "Auto-confirmed after booking"}</div>
          </div>
        )}
        <Button className="mt-5 w-full" disabled={!slotId || saving || missingRequired || detail?.resources.length === 0}>
          <CalendarDays size={17} />
          {!auth.user
            ? "Sign in to confirm"
            : saving
              ? "Confirming"
              : detail?.is_paid
                ? "Continue to payment"
                : "Confirm booking"}
        </Button>
        <div className="mt-4 rounded-md border border-line bg-white p-3 text-sm">
          <div className="font-semibold text-ink">Calendar access</div>
          <p className="mt-1 text-neutral-600">Connect Google Calendar to check conflicts before you book.</p>
          <Button type="button" variant="secondary" className="mt-3 w-full" onClick={openGoogleCalendar}>
            <CalendarDays size={16} />
            Open Google Calendar
          </Button>
        </div>
      </aside>
    </form>
  )
}

async function findNextAvailableDate(appointmentTypeId: string, resourceId: string | undefined, fromDate: string) {
  for (let offset = 1; offset <= 14; offset += 1) {
    const candidate = addDaysIso(fromDate, offset)
    const slots = await availability({
      appointment_type_id: appointmentTypeId,
      resource_id: resourceId,
      date: candidate,
      tz_offset_minutes: -new Date().getTimezoneOffset(),
    })
    if (slots.length > 0) {
      return { date: candidate, slots }
    }
  }
  return null
}
