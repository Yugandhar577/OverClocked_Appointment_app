import { Check } from "lucide-react"
import { useEffect, useState } from "react"

import { confirmBooking, organiserBookings } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import type { Booking } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { StatusBadge } from "../../components/ui/StatusBadge"
import { formatDateTime } from "../../lib/format"

export function OrganiserBookingsPage() {
  const [items, setItems] = useState<Booking[]>([])
  const [message, setMessage] = useState("")

  function load() {
    organiserBookings()
      .then((data) => setItems(data.items))
      .catch((err) => setMessage(errorMessage(err)))
  }

  useEffect(load, [])

  async function confirm(id: string) {
    try {
      await confirmBooking(id)
      load()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <div className="grid gap-5">
      <h1 className="border-b border-line pb-4 text-3xl font-bold text-ink">Bookings</h1>
      {message && <Notice>{message}</Notice>}
      <div className="overflow-hidden rounded-md border border-line bg-paper">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-white">
            <tr>
              <Th>Appointment</Th>
              <Th>Time</Th>
              <Th>Status</Th>
              <Th>Code</Th>
              <Th>Action</Th>
            </tr>
          </thead>
          <tbody>
            {items.map((booking) => (
              <tr key={booking.id} className="border-t border-line">
                <Td>{booking.appointment_title}</Td>
                <Td>{formatDateTime(booking.slot_start)}</Td>
                <Td>
                  <StatusBadge status={booking.status} />
                </Td>
                <Td>{booking.confirmation_code}</Td>
                <Td>
                  {booking.status === "pending" && (
                    <Button variant="secondary" onClick={() => confirm(booking.id)}>
                      <Check size={16} />
                    </Button>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-bold">{children}</th>
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-3">{children}</td>
}
