import { CalendarDays, CalendarPlus, RefreshCcw, XCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, Navigate } from "react-router-dom"

import { googleCalendarConnect } from "../../api/advanced"
import { cancelBooking, myAppointments } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { Booking } from "../../api/types"
import { useAuth } from "../../auth/useAuth"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { Skeleton } from "../../components/ui/Skeleton"
import { StatusBadge } from "../../components/ui/StatusBadge"
import { formatDateTime } from "../../lib/format"

export function MyAppointmentsPage() {
  const { hasRole } = useAuth()
  const pageSize = 8
  const [status, setStatus] = useState("upcoming")
  const [items, setItems] = useState<Booking[]>([])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const isAdminOnly = hasRole("admin") && !hasRole("customer")
  const isOrganiserOnly = hasRole("organiser") && !hasRole("customer") && !hasRole("admin")

  function load(nextPage = 1, append = false) {
    setError("")
    if (append) {
      setLoadingMore(true)
    } else {
      setLoading(true)
    }
    myAppointments(status, nextPage, pageSize)
      .then((data) => {
        setItems((current) => (append ? [...current, ...data.items] : data.items))
        setPage(data.page)
        setTotal(data.total)
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => {
        setLoading(false)
        setLoadingMore(false)
      })
  }

  useEffect(() => load(1, false), [status])

  async function cancel(id: string) {
    if (!window.confirm("Cancel this booking?")) return
    setError("")
    try {
      await cancelBooking(id, "customer_cancelled")
      load(1, false)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function openGoogleCalendar() {
    const response = await googleCalendarConnect()
    window.open(response.auth_url, "_blank", "noopener,noreferrer")
  }

  if (isAdminOnly) return <Navigate to="/admin" replace />
  if (isOrganiserOnly) return <Navigate to="/organiser/types" replace />

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
              <Th>Calendar</Th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              Array.from({ length: 5 }, (_, index) => (
                <tr key={`skeleton-${index}`} className="border-t border-line">
                  <Td><Skeleton className="h-10 w-48 bg-white" /></Td>
                  <Td><Skeleton className="h-4 w-36 bg-white" /></Td>
                  <Td><Skeleton className="h-8 w-24 rounded-full bg-white" /></Td>
                  <Td><Skeleton className="h-4 w-28 bg-white" /></Td>
                  <Td><Skeleton className="h-10 w-24 bg-white" /></Td>
                  <Td><Skeleton className="h-10 w-24 bg-white" /></Td>
                </tr>
              ))}
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
                <Td>
                  <Button variant="secondary" onClick={openGoogleCalendar} title="Open in Google Calendar">
                    <CalendarDays size={16} />
                    Add
                  </Button>
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
      {items.length < total && (
        <div className="flex justify-center">
          <Button type="button" variant="secondary" onClick={() => load(page + 1, true)} disabled={loadingMore}>
            {loadingMore ? "Loading..." : `Load more appointments (${items.length}/${total})`}
          </Button>
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
