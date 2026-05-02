import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  Building2,
  CalendarClock,
  RefreshCw,
  UserSquare2,
  Users,
  Zap,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { adminStats } from "../../api/admin"
import { errorMessage } from "../../api/client"
import { listOrganizations } from "../../api/organizations"
import type { ActivityEvent } from "../../lib/adminMockData"
import { MOCK_ENABLED, getOrgStatusBreakdown, mockGetRecentActivity } from "../../lib/adminMockData"
import { Notice } from "../../components/ui/Notice"

const STATUS_COLORS: Record<string, string> = {
  confirmed: "#275efe",
  pending: "#a5533d",
  completed: "#44624a",
  cancelled: "#b42318",
}

const ACTIVITY_ICONS: Record<string, string> = {
  user_joined: "🧑",
  org_created: "🏢",
  org_flagged: "🚩",
  user_deactivated: "🔒",
  role_changed: "🛡️",
  booking_made: "📅",
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
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [orgStatusBreakdown, setOrgStatusBreakdown] = useState<Record<string, number>>({})
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [lastRefreshed, setLastRefreshed] = useState(new Date())

  const load = useCallback(() => {
    setLoading(true)
    Promise.all([
      adminStats().then(setStats).catch((err) => setError(errorMessage(err))),
      listOrganizations({ page: 1, page_size: 100 }).then((data) => {
        setTotalOrgs(data.total)
        const attention = data.items
          .filter((o) => ["flagged", "suspended", "aborted"].includes(o.status))
          .map((o) => ({ name: o.name, id: o.id, status: o.status }))
        setFlaggedOrgs(attention)
      }).catch(() => {}),
    ]).finally(() => {
      setLastRefreshed(new Date())
      setLoading(false)
    })
    if (MOCK_ENABLED) {
      setOrgStatusBreakdown(getOrgStatusBreakdown())
      mockGetRecentActivity().then(setActivity)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const statusChartData = useMemo(() => {
    if (!stats?.appointments_by_status) return []
    return Object.entries(stats.appointments_by_status).map(([name, value]) => ({ name, value }))
  }, [stats])

  const orgHealthData = useMemo(() => {
    return Object.entries(orgStatusBreakdown).map(([name, value]) => ({ name, value }))
  }, [orgStatusBreakdown])

  if (error && !stats) return <Notice tone="error">{error}</Notice>

  return (
    <div className="grid gap-8">
      {/* ── hero ────────────────────────────────────────────────────── */}
      <header className="relative overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-ink via-[#1e2a1e] to-moss p-8 text-paper shadow-panel">
        <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-signal/15 blur-3xl" aria-hidden />
        <div className="absolute bottom-0 left-0 h-32 w-32 rounded-full bg-moss/20 blur-2xl" aria-hidden />
        <div className="relative flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-paper/60">Admin console · System overview</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">Dashboard</h1>
            <p className="mt-2 max-w-lg text-sm text-paper/75">
              Real-time metrics across all users, service providers, organizations, and bookings.
            </p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-xs font-semibold text-paper/90 transition hover:bg-white/20 disabled:opacity-50"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            {loading ? "Refreshing…" : `Updated ${timeAgo(lastRefreshed.toISOString())}`}
          </button>
        </div>
      </header>

      {/* ── metric tiles ────────────────────────────────────────────── */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile icon={<Users className="text-signal" size={22} />} label="Total users" value={stats?.total_users ?? 0} hint="All registered accounts" />
        <MetricTile icon={<UserSquare2 className="text-moss" size={22} />} label="Service providers" value={stats?.total_organisers ?? 0} hint="Organiser-role accounts" />
        <MetricTile icon={<Building2 className="text-clay" size={22} />} label="Organizations" value={totalOrgs ?? 0} hint="Registered tenant orgs" />
        <MetricTile icon={<CalendarClock className="text-paper" size={22} />} label="Total appointments" value={stats?.total_appointments ?? 0} hint="All booking records" dark />
      </section>

      {/* ── charts row ──────────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-line bg-white p-6 shadow-panel">
          <h2 className="text-base font-bold text-ink">Appointments by status</h2>
          <p className="mt-0.5 text-xs text-neutral-500">Booking lifecycle breakdown</p>
          <div className="mt-4 h-48">
            {statusChartData.length === 0 ? (
              <p className="text-sm text-neutral-400">No appointment data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusChartData} layout="vertical" margin={{ left: 8, right: 16, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e2d9" />
                  <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fontWeight: 600 }} tickLine={false} axisLine={false} width={80} />
                  <Tooltip cursor={{ fill: "#f8f7f2" }} contentStyle={{ borderRadius: 8, border: "1px solid #d7d2c6", fontSize: 12 }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {statusChartData.map((entry, i) => (
                      <Cell key={i} fill={STATUS_COLORS[entry.name] ?? "#161616"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {MOCK_ENABLED && orgHealthData.length > 0 ? (
          <div className="rounded-2xl border border-line bg-white p-6 shadow-panel">
            <h2 className="text-base font-bold text-ink">Organization health</h2>
            <p className="mt-0.5 text-xs text-neutral-500">Status distribution across tenants</p>
            <div className="mt-4 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={orgHealthData} layout="vertical" margin={{ left: 8, right: 16, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e2d9" />
                  <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fontWeight: 600 }} tickLine={false} axisLine={false} width={80} />
                  <Tooltip cursor={{ fill: "#f8f7f2" }} contentStyle={{ borderRadius: 8, border: "1px solid #d7d2c6", fontSize: 12 }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} fill="#44624a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <div className="grid content-start gap-4">
            <QuickLink to="/admin/users" icon={<Users size={18} />} title="User & provider management" desc={`${stats?.total_users ?? 0} accounts · Filter, activate, assign roles`} />
            <QuickLink to="/admin/organizations" icon={<Building2 size={18} />} title="Organizations" desc={`${totalOrgs ?? 0} tenants · Domains and lifecycle actions`} />
          </div>
        )}
      </div>

      {/* ── alerts + activity ────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* flagged / suspended orgs */}
        {flaggedOrgs.length > 0 && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-panel">
            <div className="flex items-center gap-2">
              <AlertTriangle size={17} className="text-amber-700" />
              <h2 className="text-sm font-bold text-amber-900">Requires attention ({flaggedOrgs.length})</h2>
            </div>
            <p className="mt-1 text-xs text-amber-700">Organizations with flagged, suspended, or aborted status.</p>
            <ul className="mt-4 grid gap-2">
              {flaggedOrgs.map((o) => (
                <li key={o.id}>
                  <Link to={`/admin/organizations/${o.id}`} className="flex items-center justify-between rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm transition hover:border-amber-400">
                    <span className="font-semibold text-ink">{o.name}</span>
                    <StatusBadge status={o.status} />
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* recent activity */}
        {activity.length > 0 && (
          <div className="rounded-2xl border border-line bg-white p-5 shadow-panel">
            <div className="flex items-center gap-2">
              <Zap size={15} className="text-signal" />
              <h2 className="text-sm font-bold text-ink">Recent activity</h2>
            </div>
            <ul className="mt-4 grid gap-1">
              {activity.map((ev) => (
                <li key={ev.id} className="flex items-start gap-2.5 border-b border-line py-2.5 last:border-0">
                  <span className="mt-0.5 text-sm">{ACTIVITY_ICONS[ev.type] ?? "•"}</span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-ink">{ev.summary}</p>
                    <p className="text-xs text-neutral-500">{timeAgo(ev.timestamp)}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* quick links when no mock */}
        {!MOCK_ENABLED && (
          <div className="grid content-start gap-4">
            <QuickLink to="/admin/users" icon={<Users size={18} />} title="User & provider management" desc="Filter, activate, and assign roles" />
            <QuickLink to="/admin/organizations" icon={<Building2 size={18} />} title="Organizations" desc="Tenants, domains, and lifecycle actions" />
          </div>
        )}

        {/* platform checklist */}
        <div className="rounded-2xl border border-line bg-white p-5 shadow-panel">
          <div className="flex items-center gap-2">
            <BadgeCheck size={15} className="text-moss" />
            <h2 className="text-sm font-bold text-ink">Platform checklist</h2>
          </div>
          <ul className="mt-4 grid gap-2 text-sm">
            {[
              { label: "Default roles seeded", ok: true },
              { label: "Admin account exists", ok: (stats?.total_users ?? 0) > 0 },
              { label: "Service providers registered", ok: (stats?.total_organisers ?? 0) > 0 },
              { label: "Organizations created", ok: (totalOrgs ?? 0) > 0 },
              { label: "Appointments recorded", ok: (stats?.total_appointments ?? 0) > 0 },
            ].map(({ label, ok }) => (
              <li key={label} className="flex items-center gap-2">
                <span className={ok ? "text-moss" : "text-neutral-400"}>{ok ? "✓" : "○"}</span>
                <span className={ok ? "text-ink" : "text-neutral-500"}>{label}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

function MetricTile({ label, value, hint, icon, dark }: { label: string; value: number; hint: string; icon: React.ReactNode; dark?: boolean }) {
  return (
    <div className={["rounded-2xl border p-5 shadow-panel", dark ? "border-ink bg-ink text-paper" : "border-line bg-white text-ink"].join(" ")}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className={["text-xs font-bold uppercase tracking-wider", dark ? "text-paper/60" : "text-neutral-500"].join(" ")}>{label}</div>
          <div className="mt-2 text-3xl font-bold tabular-nums">{value.toLocaleString()}</div>
          <div className={["mt-2 text-xs", dark ? "text-paper/70" : "text-neutral-600"].join(" ")}>{hint}</div>
        </div>
        <div className={["grid h-11 w-11 shrink-0 place-items-center rounded-xl", dark ? "bg-white/10" : "bg-paper"].join(" ")}>{icon}</div>
      </div>
    </div>
  )
}

function QuickLink({ to, title, desc, icon }: { to: string; title: string; desc: string; icon: React.ReactNode }) {
  return (
    <Link to={to} className="group flex items-center justify-between rounded-2xl border border-line bg-white p-5 shadow-panel transition hover:border-ink">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-paper text-neutral-600 group-hover:bg-ink group-hover:text-paper transition">{icon}</div>
        <div>
          <div className="text-sm font-bold text-ink">{title}</div>
          <div className="mt-0.5 text-xs text-neutral-600">{desc}</div>
        </div>
      </div>
      <ArrowRight className="shrink-0 text-neutral-400 transition group-hover:translate-x-0.5 group-hover:text-ink" size={18} />
    </Link>
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
  return (
    <span className={["rounded-full px-2 py-0.5 text-xs font-bold", styles[status] ?? "bg-paper text-ink"].join(" ")}>
      {status}
    </span>
  )
}
