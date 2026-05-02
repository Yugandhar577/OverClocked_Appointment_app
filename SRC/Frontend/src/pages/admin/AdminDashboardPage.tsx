import {
  BarChart3,
  Building2,
  CalendarClock,
  Download,
  LayoutGrid,
  List,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Users,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { adminStats } from "../../api/admin"
import { errorMessage } from "../../api/client"
import { listOrganizations } from "../../api/organizations"
import { Notice } from "../../components/ui/Notice"

const STATUS_COLORS: Record<string, string> = {
  confirmed: "#017E84",
  pending: "#F0AD4E",
  completed: "#28A745",
  cancelled: "#DC3545",
  no_show: "#714B67",
}

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return "just now"
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export function AdminDashboardPage() {
  const [stats, setStats] = useState<Awaited<ReturnType<typeof adminStats>> | null>(null)
  const [totalOrgs, setTotalOrgs] = useState<number | null>(null)
  const [flaggedOrgs, setFlaggedOrgs] = useState<{ name: string; id: string; status: string }[]>([])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [lastRefreshed, setLastRefreshed] = useState(new Date())

  const load = useCallback(() => {
    setLoading(true)
    setError("")
    Promise.all([
      adminStats().then(setStats).catch((err) => setError(errorMessage(err))),
      listOrganizations({ page: 1, page_size: 100 })
        .then((data) => {
          setTotalOrgs(data.total)
          setFlaggedOrgs(
            data.items
              .filter((org) => ["flagged", "suspended", "aborted"].includes(org.status))
              .map((org) => ({ name: org.name, id: org.id, status: org.status })),
          )
        })
        .catch(() => {}),
    ]).finally(() => {
      setLastRefreshed(new Date())
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const statusChartData = useMemo(() => {
    if (!stats?.appointments_by_status) return []
    return Object.entries(stats.appointments_by_status).map(([name, value]) => ({ name, value }))
  }, [stats])

  if (error && !stats) return <Notice tone="error">{error}</Notice>

  const rows = [
    { label: "Users", count: stats?.total_users ?? 0, href: "/admin/users" },
    { label: "Service Providers", count: stats?.total_organisers ?? 0, href: "/admin/users" },
    { label: "Customers", count: stats?.total_customers ?? 0, href: "/admin/users" },
    { label: "Organizations", count: totalOrgs ?? 0, href: "/admin/organizations" },
    { label: "Appointments", count: stats?.total_appointments ?? 0, href: "/admin/analytics" },
  ]

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 border-b border-line pb-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <Link to="/admin/users" className="rounded-md bg-[var(--odoo-primary)] px-4 py-2 text-sm font-bold text-white">
            New
          </Link>
          <div>
            <h1 className="text-2xl font-semibold text-ink">Dashboard</h1>
            <p className="text-sm text-neutral-600">System overview for users, organizations, and appointments</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex h-10 min-w-72 items-center gap-2 rounded-md border border-line bg-white px-3">
            <Search size={17} className="text-neutral-500" />
            <span className="rounded bg-[var(--odoo-sidebar)] px-2 py-1 text-xs font-semibold text-neutral-700">Admin</span>
            <input className="min-w-0 flex-1 bg-transparent text-sm outline-none" placeholder="Search..." />
            <SlidersHorizontal size={16} className="text-neutral-500" />
          </div>
          <button className="grid h-10 w-10 place-items-center rounded-md border border-line bg-white text-ink">
            <BarChart3 size={17} />
          </button>
          <button className="grid h-10 w-10 place-items-center rounded-md border border-line bg-white text-ink">
            <LayoutGrid size={17} />
          </button>
          <button className="grid h-10 w-10 place-items-center rounded-md border border-line bg-white text-ink">
            <List size={17} />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={load}
          disabled={loading}
          className="inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          {loading ? "Refreshing" : `Updated ${timeAgo(lastRefreshed.toISOString())}`}
        </button>
        <button className="inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink">
          <Download size={16} />
          Export
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Kpi icon={<Users size={18} />} label="Total Users" value={stats?.total_users ?? 0} />
        <Kpi icon={<Building2 size={18} />} label="Organizations" value={totalOrgs ?? 0} />
        <Kpi icon={<CalendarClock size={18} />} label="Appointments" value={stats?.total_appointments ?? 0} />
        <Kpi icon={<RefreshCw size={18} />} label="Attention" value={flaggedOrgs.length} tone={flaggedOrgs.length > 0 ? "warning" : "ok"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <div className="overflow-hidden rounded-md border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-semibold text-ink">System Pivot</h2>
          </div>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-[var(--odoo-sidebar)] text-left text-neutral-600">
                <th className="border-b border-line px-4 py-3 font-semibold">Metric</th>
                <th className="border-b border-line px-4 py-3 text-right font-semibold">Count</th>
                <th className="border-b border-line px-4 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border-b border-line px-4 py-3 font-semibold">Total</td>
                <td className="border-b border-line px-4 py-3 text-right font-bold">{rows.reduce((sum, row) => sum + row.count, 0)}</td>
                <td className="border-b border-line px-4 py-3 text-neutral-500">Overview</td>
              </tr>
              {rows.map((row) => (
                <tr key={row.label} className="hover:bg-[#fbf7ef]">
                  <td className="border-b border-line px-8 py-3">{row.label}</td>
                  <td className="border-b border-line px-4 py-3 text-right font-semibold">{row.count}</td>
                  <td className="border-b border-line px-4 py-3">
                    <Link className="font-semibold text-[var(--odoo-primary)]" to={row.href}>Open</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-4">
          <div className="rounded-md border border-line bg-white p-4">
            <h2 className="font-semibold text-ink">Appointments by Status</h2>
            <div className="mt-4 h-52">
              {statusChartData.length === 0 ? (
                <p className="text-sm text-neutral-500">No appointment data yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusChartData} layout="vertical" margin={{ left: 6, right: 12 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#D8DADD" />
                    <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <YAxis dataKey="name" type="category" width={78} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ borderRadius: 6, border: "1px solid #D8DADD", fontSize: 12 }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} fill="#017E84" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="rounded-md border border-line bg-white">
            <div className="border-b border-line px-4 py-3">
              <h2 className="font-semibold text-ink">Requires Attention</h2>
            </div>
            <div className="divide-y divide-line">
              {flaggedOrgs.length === 0 && <p className="px-4 py-5 text-sm text-neutral-500">No flagged organizations.</p>}
              {flaggedOrgs.map((org) => (
                <Link key={org.id} to={`/admin/organizations/${org.id}`} className="flex items-center justify-between px-4 py-3 text-sm hover:bg-[#fbf7ef]">
                  <span className="font-semibold text-ink">{org.name}</span>
                  <StatusBadge status={org.status} />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Kpi({ label, value, icon, tone = "default" }: { label: string; value: number; icon: React.ReactNode; tone?: "default" | "warning" | "ok" }) {
  const toneClass = tone === "warning" ? "text-amber-700 bg-amber-50" : tone === "ok" ? "text-emerald-700 bg-emerald-50" : "text-[var(--odoo-primary)] bg-[#f5efe3]"
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-wide text-neutral-500">{label}</p>
        <span className={`grid h-9 w-9 place-items-center rounded-md ${toneClass}`}>{icon}</span>
      </div>
      <div className="mt-3 text-3xl font-bold text-ink">{value.toLocaleString()}</div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-emerald-50 text-emerald-800",
    inactive: "bg-neutral-100 text-neutral-600",
    flagged: "bg-red-50 text-red-700",
    suspended: "bg-amber-50 text-amber-800",
    aborted: "bg-neutral-200 text-neutral-700",
  }
  return <span className={`rounded-full px-2 py-1 text-xs font-bold ${styles[status] ?? "bg-paper text-ink"}`}>{status}</span>
}
