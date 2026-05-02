import { useEffect, useState } from "react"

import { errorMessage } from "../../api/client"
import { listWaitlist, type WaitlistEntry } from "../../api/advanced"
import { Notice } from "../../components/ui/Notice"

export function WaitlistDashboardPage() {
  const [items, setItems] = useState<WaitlistEntry[]>([])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listWaitlist()
      .then(setItems)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ink">Waitlist</h1>
        <p className="text-sm text-neutral-600">Track customers waiting for full slots and cancelled-slot offers.</p>
      </div>
      {error && <Notice tone="error">{error}</Notice>}
      <div className="odoo-surface overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-[var(--odoo-border)] bg-[var(--odoo-sidebar)] text-xs uppercase text-neutral-500">
            <tr>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Appointment Type</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td className="px-4 py-6 text-neutral-500" colSpan={5}>Loading waitlist...</td></tr>}
            {!loading && items.length === 0 && <tr><td className="px-4 py-6 text-neutral-500" colSpan={5}>No waitlist entries yet.</td></tr>}
            {items.map((item) => (
              <tr key={item.id} className="border-b border-[var(--odoo-border)] last:border-0">
                <td className="px-4 py-3 font-mono text-xs">{item.customer_id}</td>
                <td className="px-4 py-3 font-mono text-xs">{item.appointment_type_id}</td>
                <td className="px-4 py-3 capitalize">{item.status}</td>
                <td className="px-4 py-3">{item.priority}</td>
                <td className="px-4 py-3">{new Date(item.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
