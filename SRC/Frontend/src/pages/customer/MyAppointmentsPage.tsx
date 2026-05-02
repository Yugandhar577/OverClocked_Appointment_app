import { CalendarPlus, RefreshCcw, XCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { cancelBooking, myAppointments } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { Booking } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { StatusBadge } from "../../components/ui/StatusBadge"
import { formatDateTime } from "../../lib/format"

export function MyAppointmentsPage() {
  const [status, setStatus] = useState("upcoming")
  const [items, setItems] = useState<Booking[]>([])
  const [error, setError] = useState("")

  function load() {
    myAppointments(status)
      .then((data) => setItems(data.items))
      .catch((err) => setError(errorMessage(err)))
  }

  useEffect(load, [status])

  async function cancel(id: string) {
    if (!window.confirm("Cancel this booking?")) return
    setError("")
    try {
      await cancelBooking(id, "customer_cancelled")
      load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div className="grid gap-5">
      <div className="flex flex-col justify-between gap-3 border-b border-line pb-4 md:flex-row md:items-center">
        <h1 className="text-3xl font-bold text-ink">My appointments</h1>
        <div className="flex gap-2">
          {["upcoming", "past"].map((value) => (
            <Button key={value} variant={status === value ? "primary" : "secondary"} onClick={() => setStatus(value)}>
              {value}
            </Button>
          ))}
        </div>
      </div>
      {error && <Notice tone="error">{error}</Notice>}
      <div className="overflow-hidden rounded-md border border-line bg-paper">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead className="bg-white text-left">
            <tr>
              <Th>Appointment</Th>
              <Th>Time</Th>
              <Th>Status</Th>
              <Th>Code</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {items.map((booking) => (
              <tr key={booking.id} className="border-t border-line">
                <Td>
                  <div className="font-semibold">{booking.appointment_title}</div>
                  <div className="text-xs text-neutral-600">{booking.venue}</div>
                </Td>
                <Td>{formatDateTime(booking.slot_start)}</Td>
                <Td>
                  <StatusBadge status={booking.status} />
                </Td>
                <Td>{booking.confirmation_code}</Td>
                <Td>
                  {["pending", "confirmed"].includes(booking.status) ? (
                    <div className="flex gap-2">
                      <Link to={`/booking/${booking.id}/reschedule`}>
                        <Button variant="secondary" title="Reschedule">
                          <RefreshCcw size={16} />
                        </Button>
                      </Link>
                      <Button variant="danger" onClick={() => cancel(booking.id)} title="Cancel">
                        <XCircle size={16} />
                      </Button>
                    </div>
                  ) : (
                    <span className="text-xs font-semibold text-neutral-500">Closed</span>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {items.length === 0 && (
        <div className="rounded-md border border-line bg-paper p-5">
          <Notice>No appointments in this view.</Notice>
          <Link className="mt-4 inline-flex" to="/">
            <Button>
              <CalendarPlus size={17} />
              Book appointment
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-bold text-ink">{children}</th>
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-3 text-ink">{children}</td>
}
