import { CalendarCheck, CalendarPlus, RefreshCcw } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"

import { getBooking } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { Booking } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { StatusBadge } from "../../components/ui/StatusBadge"
import { formatDateTime } from "../../lib/format"

function googleCalendarUrl(booking: Booking): string {
  const title = encodeURIComponent(booking.appointment_title ?? "Appointment")
  const location = encodeURIComponent(booking.venue ?? "")

  function toGcalDateTime(iso: string | null | undefined) {
    if (!iso) return ""
    return new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "")
  }

  const start = toGcalDateTime(booking.slot_start)
  const end = toGcalDateTime(booking.slot_end)
  const dates = start && end ? `${start}/${end}` : start

  const details = encodeURIComponent(
    `Booking reference: ${booking.confirmation_code}\nPeople: ${booking.people_count}`,
  )

  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${dates}&details=${details}&location=${location}`
}

export function ConfirmationPage() {
  const { bookingId } = useParams()
  const [booking, setBooking] = useState<Booking | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!bookingId) return
    getBooking(bookingId)
      .then(setBooking)
      .catch((err) => setError(errorMessage(err)))
  }, [bookingId])

  if (error) return <Notice tone="error">{error}</Notice>
  if (!booking) return <Notice>Loading confirmation...</Notice>

  const canAddToCalendar = ["pending", "confirmed"].includes(booking.status) && Boolean(booking.slot_start)

  return (
    <div className="mx-auto max-w-2xl rounded-md border border-line bg-paper p-6 shadow-panel">
      <div className="flex items-start gap-4">
        <div className="grid h-12 w-12 place-items-center rounded-md bg-moss text-white">
          <CalendarCheck />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold text-ink">Booking {booking.confirmation_code}</h1>
            <StatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-sm text-neutral-700">{booking.appointment_title}</p>
        </div>
      </div>
      <dl className="mt-6 grid gap-3 border-t border-line pt-5 text-sm">
        <Row label="Time" value={formatDateTime(booking.slot_start)} />
        <Row label="Venue" value={booking.venue ?? "-"} />
        <Row label="People" value={String(booking.people_count)} />
      </dl>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/me/appointments">
          <Button>My appointments</Button>
        </Link>
        {canAddToCalendar && (
          <a href={googleCalendarUrl(booking)} target="_blank" rel="noopener noreferrer">
            <Button variant="secondary">
              <CalendarPlus size={17} />
              Add to Google Calendar
            </Button>
          </a>
        )}
        {["pending", "confirmed"].includes(booking.status) && (
          <Link to={`/booking/${booking.id}/reschedule`}>
            <Button variant="secondary">
              <RefreshCcw size={17} />
              Reschedule
            </Button>
          </Link>
        )}
        <Link to="/">
          <Button variant="secondary">Book another</Button>
        </Link>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-neutral-600">{label}</dt>
      <dd className="font-semibold text-ink">{value}</dd>
    </div>
  )
}
