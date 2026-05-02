import { CalendarDays, Check, Clock, Search, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { confirmBooking, organiserBookings, organiserCancelBooking } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { Booking } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { Skeleton } from "../../components/ui/Skeleton"
import { StatusBadge } from "../../components/ui/StatusBadge"
import { formatDateTime } from "../../lib/format"

export function OrganiserBookingsPage() {
  const pageSize = 8
  const [items, setItems] = useState<Booking[]>([])
  const [message, setMessage] = useState("")
  const [query, setQuery] = useState("")
  const [status, setStatus] = useState("all")
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  function load(nextPage = 1, append = false) {
    setMessage("")
    if (append) {
      setLoadingMore(true)
    } else {
      setLoading(true)
    }
    organiserBookings({ status, page: nextPage, pageSize })
      .then((data) => {
        setItems((current) => (append ? [...current, ...data.items] : data.items))
        setPage(data.page)
        setTotal(data.total)
      })
      .catch((err) => setMessage(errorMessage(err)))
      .finally(() => {
        setLoading(false)
        setLoadingMore(false)
      })
  }

  useEffect(() => load(1, false), [status])

  const visibleItems = useMemo(
    () =>
      items.filter((booking) => {
        const haystack = `${booking.appointment_title || ""} ${booking.confirmation_code} ${booking.venue || ""}`.toLowerCase()
        return haystack.includes(query.trim().toLowerCase())
      }),
    [items, query],
  )

  async function confirm(id: string) {
    try {
      await confirmBooking(id)
      setMessage("Appointment confirmed.")
      load(1, false)
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  async function cancel(id: string) {
    try {
      await organiserCancelBooking(id, "Cancelled by organiser")
      setMessage("Appointment cancelled.")
      load(1, false)
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-md border border-line bg-paper">
        <div className="flex flex-col gap-4 border-b border-line p-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-bold text-signal">Appointments</p>
            <h1 className="text-2xl font-bold text-ink">Manage appointments</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <Metric label="Loaded" value={items.length} icon={<CalendarDays size={18} />} />
            <Metric label="Pending" value={items.filter((item) => item.status === "pending").length} icon={<Clock size={18} />} />
          </div>
        </div>
        <div className="grid gap-3 border-b border-line bg-white/70 p-4 lg:grid-cols-[1fr_auto]">
          <label className="focus-within:ring-signal flex h-10 items-center rounded-md border border-line bg-white px-3 focus-within:ring-2">
            <Search size={18} className="text-neutral-500" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search appointments..."
              className="h-full min-w-0 flex-1 border-0 bg-transparent px-3 text-sm outline-none"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {["all", "pending", "confirmed", "cancelled", "completed"].map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setStatus(option)}
                className={`h-10 rounded-md border px-3 text-sm font-semibold capitalize ${status === option ? "border-ink bg-ink text-paper" : "border-line bg-white text-ink"}`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
        {message && <div className="p-4"><Notice>{message}</Notice></div>}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[840px] text-left text-sm">
            <thead className="bg-white">
              <tr>
                <Th>Appointment</Th>
                <Th>Customer</Th>
                <Th>Time</Th>
                <Th>Status</Th>
                <Th>Code</Th>
                <Th>Action</Th>
              </tr>
            </thead>
            <tbody>
              {loading &&
                Array.from({ length: 5 }, (_, index) => (
                  <tr key={`skeleton-${index}`} className="border-t border-line">
                    <Td><Skeleton className="h-10 w-48 bg-white" /></Td>
                    <Td><Skeleton className="h-4 w-32 bg-white" /></Td>
                    <Td><Skeleton className="h-4 w-36 bg-white" /></Td>
                    <Td><Skeleton className="h-8 w-24 rounded-full bg-white" /></Td>
                    <Td><Skeleton className="h-4 w-28 bg-white" /></Td>
                    <Td><Skeleton className="h-10 w-24 bg-white" /></Td>
                  </tr>
                ))}
              {visibleItems.map((booking) => (
                <tr key={booking.id} className="border-t border-line">
                  <Td>
                    <strong>{booking.appointment_title}</strong>
                    <div className="text-xs text-neutral-600">{booking.venue || "No venue"}</div>
                  </Td>
                  <Td>{booking.customer_full_name || booking.customer_email || "Customer"}</Td>
                  <Td>{formatDateTime(booking.slot_start)}</Td>
                  <Td><StatusBadge status={booking.status} /></Td>
                  <Td>{booking.confirmation_code}</Td>
                  <Td>
                    <div className="flex gap-2">
                      {booking.status === "pending" && (
                        <Button type="button" variant="secondary" onClick={() => confirm(booking.id)} title="Confirm">
                          <Check size={16} />
                        </Button>
                      )}
                      {booking.status !== "cancelled" && booking.status !== "completed" && (
                        <Button type="button" variant="ghost" onClick={() => cancel(booking.id)} title="Cancel">
                          <X size={16} />
                        </Button>
                      )}
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {visibleItems.length === 0 && <div className="p-4"><Notice>No appointments match this view.</Notice></div>}
        {items.length < total && (
          <div className="border-t border-line p-4 text-center">
            <Button type="button" variant="secondary" onClick={() => load(page + 1, true)} disabled={loadingMore}>
              {loadingMore ? "Loading..." : `Load more bookings (${items.length}/${total})`}
            </Button>
          </div>
        )}
      </section>
    </div>
  )
}

function Metric({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="flex min-w-36 items-center gap-3 rounded-md border border-line bg-white px-3 py-2">
      <span className="text-signal">{icon}</span>
      <span className="text-sm">{label}<br /><strong>{value}</strong></span>
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-bold">{children}</th>
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-3 align-top">{children}</td>
}
