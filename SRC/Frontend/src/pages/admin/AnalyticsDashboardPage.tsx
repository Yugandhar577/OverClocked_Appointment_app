import { useEffect, useState } from "react"

import { getAnalytics, type AnalyticsSummary } from "../../api/advanced"
import { errorMessage } from "../../api/client"
import { Notice } from "../../components/ui/Notice"

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="odoo-surface p-4">
      <div className="text-xs font-semibold uppercase text-neutral-500">{label}</div>
      <div className="mt-2 text-3xl font-bold text-primary">{value}</div>
    </div>
  )
}

export function AnalyticsDashboardPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    getAnalytics().then(setData).catch((err) => setError(errorMessage(err)))
  }, [])

  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Appointment Analytics</h1>
        <p className="text-sm text-neutral-600">Booking totals, cancellations, no-shows, waitlist conversion, and service demand.</p>
      </div>
      {error && <Notice tone="error">{error}</Notice>}
      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Total bookings" value={data?.total_bookings ?? "..."} />
        <Metric label="Completed" value={data?.completed_bookings ?? "..."} />
        <Metric label="Cancelled" value={data?.cancelled_bookings ?? "..."} />
        <Metric label="No-shows" value={data?.no_shows ?? "..."} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="odoo-surface p-4">
          <h2 className="font-semibold text-ink">Waitlist conversion</h2>
          <p className="mt-3 text-4xl font-bold text-[var(--odoo-secondary)]">{Math.round((data?.waitlist_conversion_rate ?? 0) * 100)}%</p>
        </div>
        <div className="odoo-surface p-4">
          <h2 className="font-semibold text-ink">Most booked services</h2>
          <div className="mt-3 space-y-2">
            {(data?.most_booked_services ?? []).map((service) => (
              <div key={service.service} className="flex justify-between border-b border-[var(--odoo-border)] py-2 text-sm">
                <span>{service.service}</span>
                <strong>{service.count}</strong>
              </div>
            ))}
            {data && data.most_booked_services.length === 0 && <p className="text-sm text-neutral-500">No bookings yet.</p>}
          </div>
        </div>
      </div>
    </section>
  )
}
