import { useEffect, useState } from "react"

import { adminStats } from "../../api/admin"
import { errorMessage } from "../../api/client"
import { Notice } from "../../components/ui/Notice"

export function AdminStatsPage() {
  const [stats, setStats] = useState<Awaited<ReturnType<typeof adminStats>> | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    adminStats()
      .then(setStats)
      .catch((err) => setError(errorMessage(err)))
  }, [])

  if (error) return <Notice tone="error">{error}</Notice>
  if (!stats) return <Notice>Loading stats...</Notice>

  return (
    <div className="grid gap-5">
      <h1 className="border-b border-line pb-4 text-3xl font-bold text-ink">Stats</h1>
      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Users" value={stats.total_users} />
        <Metric label="Organisers" value={stats.total_organisers} />
        <Metric label="Customers" value={stats.total_customers} />
        <Metric label="Appointments" value={stats.total_appointments} />
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-paper p-4 shadow-panel">
      <div className="text-sm font-semibold text-neutral-600">{label}</div>
      <div className="mt-2 text-3xl font-bold text-ink">{value}</div>
    </div>
  )
}
