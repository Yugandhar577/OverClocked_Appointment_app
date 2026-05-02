import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"

import { availability, getBooking, rescheduleBooking } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { AvailabilitySlot, Booking } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"
import { formatDateTime, formatTime, todayIsoDate } from "../../lib/format"

export function ReschedulePage() {
  const { bookingId } = useParams()
  const navigate = useNavigate()
  const [booking, setBooking] = useState<Booking | null>(null)
  const [date, setDate] = useState(todayIsoDate())
  const [slots, setSlots] = useState<AvailabilitySlot[]>([])
  const [slotId, setSlotId] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    if (!bookingId) return
    getBooking(bookingId)
      .then(setBooking)
      .catch((err) => setError(errorMessage(err)))
  }, [bookingId])

  useEffect(() => {
    if (!booking) return
    availability({
      appointment_type_id: booking.appointment_type_id,
      resource_id: booking.resource_id,
      date,
      tz_offset_minutes: -new Date().getTimezoneOffset(),
    })
      .then((data) => {
        setSlots(data)
        setSlotId(data[0]?.slot_id ?? "")
      })
      .catch((err) => setError(errorMessage(err)))
  }, [booking, date])

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!bookingId || !slotId) return
    try {
      const res = await rescheduleBooking(bookingId, slotId)
      navigate(`/booking/${res.new_id}/confirmation`)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <form className="mx-auto grid max-w-3xl gap-5" onSubmit={submit}>
      <h1 className="text-3xl font-bold text-ink">Reschedule</h1>
      {error && <Notice tone="error">{error}</Notice>}
      {booking && <Notice>Current slot: {formatDateTime(booking.slot_start)}</Notice>}
      <Field label="New date">
        <Input type="date" min={todayIsoDate()} value={date} onChange={(event) => setDate(event.target.value)} />
      </Field>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
        {slots.map((slot) => (
          <button
            key={slot.slot_id}
            type="button"
            onClick={() => setSlotId(slot.slot_id)}
            className={`focus-ring rounded-md border px-3 py-2 text-sm font-semibold ${
              slotId === slot.slot_id ? "border-ink bg-ink text-paper" : "border-line bg-white"
            }`}
          >
            {formatTime(slot.start_datetime)}
          </button>
        ))}
      </div>
      <Button disabled={!slotId}>Confirm new slot</Button>
    </form>
  )
}
