import {
  AlertTriangle,
  ArrowLeft,
  BadgeCheck,
  Building2,
  CalendarDays,
  CheckCircle,
  Clock,
  History,
  LayoutGrid,
  Users,
  XCircle,
} from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"

import { errorMessage } from "../../api/client"
import {
  abortOrganization,
  activateOrganization,
  deactivateOrganization,
  getOrganization,
  patchOrganization,
  reportOrganization,
  suspendOrganization,
} from "../../api/organizations"
import type { AdminUser, OrganizationDetail } from "../../api/types"
import { MOCK_ENABLED, mockGetOrgMembers } from "../../lib/adminMockData"
import { Button } from "../../components/ui/Button"
import { Field, Input, Textarea } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const STATUS_STYLE: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-800 border-emerald-200",
  inactive: "bg-neutral-100 text-neutral-600 border-neutral-200",
  suspended: "bg-amber-50 text-amber-800 border-amber-200",
  flagged: "bg-red-50 text-red-700 border-red-200",
  aborted: "bg-neutral-200 text-neutral-700 border-neutral-300",
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  active: <CheckCircle size={13} />,
  flagged: <AlertTriangle size={13} />,
  aborted: <XCircle size={13} />,
  suspended: <AlertTriangle size={13} />,
  inactive: <Clock size={13} />,
}

const ROLE_STYLE: Record<string, string> = {
  customer: "bg-blue-50 text-blue-800",
  organiser: "bg-emerald-50 text-emerald-800",
  admin: "bg-ink text-paper",
}

function initials(name: string) {
  return name.split(" ").slice(0, 2).map((p) => p[0]?.toUpperCase() ?? "").join("")
}

function avatarColor(name: string) {
  const colors = ["#275efe", "#44624a", "#a5533d", "#6d28d9", "#0369a1", "#b45309"]
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff
  return colors[Math.abs(h) % colors.length]
}

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (diff === 0) return "today"
  if (diff === 1) return "yesterday"
  if (diff < 30) return `${diff}d ago`
  return `${Math.floor(diff / 30)}mo ago`
}

function parseAuditNotes(notes: string | null): { text: string; index: number }[] {
  if (!notes) return []
  return notes
    .split(/\n---\n/)
    .map((chunk, i) => ({ text: chunk.trim(), index: i }))
    .reverse()
}

type Tab = "overview" | "members" | "audit"

export function AdminOrganizationDetailPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const [org, setOrg] = useState<OrganizationDetail | null>(null)
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState<Tab>("overview")
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null)

  // edit state
  const [editMode, setEditMode] = useState(false)
  const [editName, setEditName] = useState("")
  const [editDomain, setEditDomain] = useState("")

  // report state
  const [reportOpen, setReportOpen] = useState(false)
  const [reportNotes, setReportNotes] = useState("")

  // confirm dialog
  const [confirmAction, setConfirmAction] = useState<null | { label: string; action: () => void; danger?: boolean }>(null)

  // members (mock only)
  const [members, setMembers] = useState<AdminUser[]>([])

  function showToast(msg: string, tone: "success" | "error") {
    setToast({ msg, tone })
    setTimeout(() => setToast(null), 3500)
  }

  function loadOrg() {
    if (!orgId) return
    getOrganization(orgId)
      .then((data) => { setOrg(data); setEditName(data.name); setEditDomain(data.domain) })
      .catch((err) => setError(errorMessage(err)))
  }

  function loadMembers() {
    if (!orgId) return
    if (MOCK_ENABLED) {
      mockGetOrgMembers(orgId).then(setMembers).catch(() => {})
    }
  }

  useEffect(() => { loadOrg(); loadMembers() }, [orgId])

  async function run(action: () => Promise<OrganizationDetail>, successMsg: string) {
    try {
      setBusy(true); setError("")
      const next = await action()
      setOrg(next)
      showToast(successMsg, "success")
    } catch (err) {
      showToast(errorMessage(err), "error")
    } finally {
      setBusy(false); setConfirmAction(null)
    }
  }

  function ask(label: string, action: () => void, danger = false) {
    setConfirmAction({ label, action, danger })
  }

  async function submitReport() {
    if (!orgId || !reportNotes.trim()) return
    await run(() => reportOrganization(orgId, reportNotes.trim()), "Report filed.")
    setReportOpen(false); setReportNotes("")
  }

  if (!orgId) return <Notice tone="error">Missing organization ID.</Notice>
  if (error && !org) return <Notice tone="error">{error}</Notice>
  if (!org) return <Notice>Loading…</Notice>

  const auditEntries = parseAuditNotes(org.admin_report_notes)

  return (
    <div className="grid gap-6">
      {toast && (
        <div className={["fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl px-4 py-3 shadow-panel text-sm font-semibold", toast.tone === "success" ? "bg-moss text-paper" : "bg-warn text-paper"].join(" ")}>
          {toast.msg}
          <button onClick={() => setToast(null)}>✕</button>
        </div>
      )}

      <Link to="/admin/organizations" className="inline-flex items-center gap-2 text-sm font-semibold text-signal hover:underline">
        <ArrowLeft size={15} /> All organizations
      </Link>

      {error && <Notice tone="error">{error}</Notice>}

      {/* ── header card ─────────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-panel">
        <div className="flex flex-col justify-between gap-5 p-6 lg:flex-row lg:items-start">
          <div className="flex items-start gap-4">
            <div
              className="grid h-14 w-14 shrink-0 place-items-center rounded-xl text-lg font-bold text-paper"
              style={{ backgroundColor: avatarColor(org.name) }}
            >
              {initials(org.name)}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold text-ink">{org.name}</h1>
                <span className={["inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-bold", STATUS_STYLE[org.status] ?? "bg-paper text-ink border-line"].join(" ")}>
                  {STATUS_ICON[org.status]} {org.status}
                </span>
              </div>
              <p className="mt-1 font-mono text-sm text-neutral-500">{org.domain}</p>
              <p className="mt-1 text-xs text-neutral-400">
                Created {timeAgo(org.created_at)} · Last updated {timeAgo(org.updated_at)}
              </p>
            </div>
          </div>

          {/* action groups */}
          <div className="flex flex-col gap-3 lg:items-end">
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" type="button" disabled={busy} onClick={() => setEditMode((v) => !v)}>
                {editMode ? "Cancel edit" : "Edit"}
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {org.status !== "active" && (
                <Button variant="secondary" type="button" disabled={busy}
                  onClick={() => ask("Activate this organization?", () => run(() => activateOrganization(org.id), "Organization activated."))}>
                  <CheckCircle size={13} /> Activate
                </Button>
              )}
              {org.status === "active" && (
                <Button variant="secondary" type="button" disabled={busy}
                  onClick={() => ask("Deactivate this organization?", () => run(() => deactivateOrganization(org.id), "Organization deactivated."))}>
                  Deactivate
                </Button>
              )}
              {org.status !== "suspended" && org.status !== "aborted" && (
                <Button variant="secondary" type="button" disabled={busy}
                  onClick={() => ask("Suspend this organization?", () => run(() => suspendOrganization(org.id), "Organization suspended."), true)}>
                  <AlertTriangle size={13} /> Suspend
                </Button>
              )}
              <Button variant="secondary" type="button" disabled={busy} onClick={() => setReportOpen(true)}>
                Report / flag
              </Button>
              {org.status !== "aborted" && (
                <Button variant="danger" type="button" disabled={busy}
                  onClick={() => ask("Abort this organization? This is destructive and hard to undo.", () => run(() => abortOrganization(org.id), "Organization aborted."), true)}>
                  <XCircle size={13} /> Abort
                </Button>
              )}
            </div>
          </div>
        </div>

        {editMode && (
          <div className="border-t border-line px-6 py-5">
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Display name"><Input value={editName} onChange={(e) => setEditName(e.target.value)} /></Field>
              <Field label="Domain"><Input value={editDomain} onChange={(e) => setEditDomain(e.target.value)} /></Field>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button variant="ghost" type="button" onClick={() => setEditMode(false)}>Cancel</Button>
                <Button type="button" disabled={busy || !editName.trim() || !editDomain.trim()}
                  onClick={() => run(() => patchOrganization(org.id, { name: editName.trim(), domain: editDomain.trim() }), "Changes saved.")}>
                  Save changes
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── stat tiles ────────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={<Users size={18} className="text-signal" />} label="Total members" value={org.total_members} />
        <StatCard icon={<BadgeCheck size={18} className="text-moss" />} label="Active members" value={org.active_members} />
        <StatCard icon={<CalendarDays size={18} className="text-clay" />} label="Published types" value={org.active_instances} />
      </div>

      {/* ── tab navigation ────────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-panel">
        <div className="flex border-b border-line">
          {([ ["overview", "Overview", <LayoutGrid size={14} />], ["members", "Members", <Users size={14} />], ["audit", "Audit log", <History size={14} />]] as [Tab, string, React.ReactNode][]).map(([id, label, icon]) => (
            <button key={id} onClick={() => setTab(id)}
              className={["flex items-center gap-2 px-5 py-3.5 text-sm font-semibold transition border-b-2", tab === id ? "border-ink text-ink" : "border-transparent text-neutral-500 hover:text-ink"].join(" ")}>
              {icon}{label}
            </button>
          ))}
        </div>

        {/* overview tab */}
        {tab === "overview" && (
          <div className="p-6">
            <dl className="grid gap-4 sm:grid-cols-2">
              <InfoRow label="Organization ID" value={<span className="font-mono text-xs">{org.id}</span>} />
              <InfoRow label="Domain" value={<span className="font-mono text-sm">{org.domain}</span>} />
              <InfoRow label="Status" value={
                <span className={["inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-bold", STATUS_STYLE[org.status] ?? ""].join(" ")}>
                  {STATUS_ICON[org.status]} {org.status}
                </span>
              } />
              <InfoRow label="Created" value={new Date(org.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })} />
              <InfoRow label="Last updated" value={timeAgo(org.updated_at)} />
              <InfoRow label="Active instances" value={org.active_instances.toString()} />
            </dl>
            {org.admin_report_notes && (
              <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
                <div className="flex items-center gap-2 text-sm font-bold text-red-800">
                  <AlertTriangle size={14} /> Admin notes on file
                </div>
                <p className="mt-2 text-xs text-red-700 line-clamp-3 whitespace-pre-wrap">{org.admin_report_notes}</p>
              </div>
            )}
          </div>
        )}

        {/* members tab */}
        {tab === "members" && (
          <div className="p-6">
            {!MOCK_ENABLED && (
              <Notice>Member list is available with mock data mode. Enable <code>VITE_ADMIN_MOCK_DATA=true</code>.</Notice>
            )}
            {MOCK_ENABLED && members.length === 0 && (
              <p className="text-sm text-neutral-500">No members in this organization.</p>
            )}
            {MOCK_ENABLED && members.length > 0 && (
              <div className="overflow-hidden rounded-xl border border-line">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-line bg-paper">
                    <tr>
                      <th className="px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-neutral-500">Member</th>
                      <th className="px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-neutral-500">Roles</th>
                      <th className="px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-neutral-500">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((m) => (
                      <tr key={m.id} className="border-t border-line">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-bold text-paper" style={{ backgroundColor: avatarColor(m.full_name) }}>
                              {initials(m.full_name)}
                            </div>
                            <div>
                              <div className="font-semibold text-ink">{m.full_name}</div>
                              <div className="text-xs text-neutral-500">{m.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {m.roles.map((r) => (
                              <span key={r} className={["rounded-full px-2 py-0.5 text-xs font-bold", ROLE_STYLE[r] ?? "bg-paper text-ink"].join(" ")}>{r}</span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <span className={["h-2 w-2 rounded-full", m.is_active ? "bg-moss" : "bg-warn"].join(" ")} />
                            <span className={m.is_active ? "text-moss text-xs font-semibold" : "text-warn text-xs font-semibold"}>
                              {m.is_active ? "Active" : "Inactive"}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* audit tab */}
        {tab === "audit" && (
          <div className="p-6">
            {auditEntries.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-10 text-neutral-400">
                <History size={32} />
                <p className="text-sm">No audit notes yet.</p>
                <button onClick={() => setReportOpen(true)} className="text-sm font-semibold text-signal hover:underline">File a report</button>
              </div>
            ) : (
              <ol className="relative border-l border-line pl-6">
                {auditEntries.map((entry, i) => (
                  <li key={entry.index} className="mb-6 last:mb-0">
                    <span className="absolute -left-1.5 flex h-3 w-3 items-center justify-center rounded-full border border-line bg-white">
                      <span className={["h-1.5 w-1.5 rounded-full", i === 0 ? "bg-warn" : "bg-neutral-400"].join(" ")} />
                    </span>
                    <div className="ml-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-neutral-500">Note #{auditEntries.length - i}</span>
                        {i === 0 && <span className="rounded-full bg-warn/10 px-1.5 py-0.5 text-xs font-bold text-warn">Latest</span>}
                      </div>
                      <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-paper px-4 py-3 text-sm text-ink">{entry.text}</pre>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>

      {/* report modal */}
      {reportOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-4 sm:items-center">
          <div className="w-full max-w-lg rounded-2xl border border-line bg-paper p-6 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-warn/10">
                <AlertTriangle size={18} className="text-warn" />
              </div>
              <div>
                <h2 className="text-base font-bold text-ink">File report for {org.name}</h2>
                <p className="text-xs text-neutral-500">Appends to audit trail · Sets status to flagged</p>
              </div>
            </div>
            <div className="mt-4">
              <Field label="Report notes">
                <Textarea rows={5} value={reportNotes} onChange={(e) => setReportNotes(e.target.value)} placeholder="Describe the issue in detail…" />
              </Field>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={() => setReportOpen(false)}>Cancel</Button>
              <Button type="button" disabled={!reportNotes.trim() || busy} onClick={submitReport}>Submit report</Button>
            </div>
          </div>
        </div>
      )}

      {/* confirm dialog */}
      {confirmAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
          <div className="w-full max-w-sm rounded-2xl border border-line bg-paper p-6 shadow-panel">
            <div className="flex items-center gap-3">
              <div className={["grid h-10 w-10 place-items-center rounded-xl", confirmAction.danger ? "bg-warn/10" : "bg-signal/10"].join(" ")}>
                {confirmAction.danger ? <AlertTriangle size={18} className="text-warn" /> : <Building2 size={18} className="text-signal" />}
              </div>
              <p className="text-sm font-semibold text-ink">{confirmAction.label}</p>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={() => setConfirmAction(null)}>Cancel</Button>
              <Button variant={confirmAction.danger ? "danger" : "primary"} type="button" onClick={confirmAction.action} disabled={busy}>
                Confirm
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-line bg-white p-5 shadow-panel">
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-paper">{icon}</div>
      <div>
        <div className="text-xs font-bold uppercase tracking-wider text-neutral-500">{label}</div>
        <div className="mt-1 text-2xl font-bold tabular-nums text-ink">{value.toLocaleString()}</div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-bold uppercase tracking-wider text-neutral-500">{label}</dt>
      <dd className="mt-1 text-sm text-ink">{value}</dd>
    </div>
  )
}
