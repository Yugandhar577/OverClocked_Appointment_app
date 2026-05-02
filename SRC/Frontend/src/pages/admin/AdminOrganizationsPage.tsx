import {
  AlertTriangle,
  Building2,
  CheckCircle,
  ChevronRight,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Search,
  X,
  XCircle,
} from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"

import { errorMessage } from "../../api/client"
import {
  abortOrganization,
  activateOrganization,
  createOrganization,
  deactivateOrganization,
  listOrganizations,
  reportOrganization,
  suspendOrganization,
} from "../../api/organizations"
import type { ListOrganizationsParams } from "../../api/organizations"
import type { OrganizationListItem } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Field, Input, Select, Textarea } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const STATUS_OPTIONS = ["", "active", "inactive", "suspended", "flagged", "aborted"] as const

const STATUS_STYLE: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-800 border-emerald-200",
  inactive: "bg-neutral-100 text-neutral-600 border-neutral-200",
  suspended: "bg-amber-50 text-amber-800 border-amber-200",
  flagged: "bg-red-50 text-red-700 border-red-200",
  aborted: "bg-neutral-200 text-neutral-700 border-neutral-300",
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  active: <CheckCircle size={11} />,
  flagged: <AlertTriangle size={11} />,
  aborted: <XCircle size={11} />,
  suspended: <AlertTriangle size={11} />,
}

function orgInitials(name: string) {
  return name.split(" ").slice(0, 2).map((w) => w[0]?.toUpperCase() ?? "").join("")
}

function orgColor(name: string) {
  const palette = ["#275efe", "#44624a", "#a5533d", "#6d28d9", "#0369a1", "#b45309"]
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff
  return palette[Math.abs(h) % palette.length]
}

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (diff === 0) return "today"
  if (diff === 1) return "yesterday"
  if (diff < 30) return `${diff}d ago`
  return `${Math.floor(diff / 30)}mo ago`
}

export function AdminOrganizationsPage() {
  const [items, setItems] = useState<OrganizationListItem[]>([])
  const [total, setTotal] = useState(0)
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({})
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState("")
  const [searchDraft, setSearchDraft] = useState("")
  const [searchApplied, setSearchApplied] = useState("")
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDomain, setNewDomain] = useState("")
  const [loading, setLoading] = useState(false)

  function showToast(msg: string, tone: "success" | "error") {
    setToast({ msg, tone })
    setTimeout(() => setToast(null), 3500)
  }

  const buildParams = useCallback((): ListOrganizationsParams => {
    const p: ListOrganizationsParams = { page, page_size: pageSize }
    if (statusFilter) p.status = statusFilter
    if (searchApplied.trim()) p.search = searchApplied.trim()
    return p
  }, [page, pageSize, statusFilter, searchApplied])

  const load = useCallback(() => {
    setLoading(true)
    listOrganizations(buildParams())
      .then((data) => { setItems(data.items); setTotal(data.total) })
      .catch((err) => showToast(errorMessage(err), "error"))
      .finally(() => setLoading(false))
  }, [buildParams])

  // count all statuses once
  useEffect(() => {
    Promise.all(
      STATUS_OPTIONS.slice(1).map((s) => listOrganizations({ page: 1, page_size: 1, status: s }).then((d) => [s, d.total] as const))
    ).then((pairs) => {
      const map: Record<string, number> = {}
      for (const [s, n] of pairs) map[s] = n
      setStatusCounts(map)
    }).catch(() => {})
  }, [])

  useEffect(() => { load() }, [load])

  function applySearch() { setPage(1); setSearchApplied(searchDraft) }
  function clearFilters() { setStatusFilter(""); setSearchDraft(""); setSearchApplied(""); setPage(1) }
  const hasFilters = statusFilter || searchApplied

  async function submitCreate() {
    try {
      await createOrganization({ name: newName.trim(), domain: newDomain.trim() })
      setCreateOpen(false); setNewName(""); setNewDomain("")
      showToast("Organization created.", "success"); load()
    } catch (err) { showToast(errorMessage(err), "error") }
  }

  async function inlineAction(id: string, action: "activate" | "deactivate" | "suspend" | "abort", orgName: string) {
    try {
      const fn = { activate: activateOrganization, deactivate: deactivateOrganization, suspend: suspendOrganization, abort: abortOrganization }[action]
      await fn(id)
      showToast(`${orgName} ${action}d.`, "success"); load()
    } catch (err) { showToast(errorMessage(err), "error") }
  }

  async function inlineReport(id: string, notes: string, orgName: string) {
    try {
      await reportOrganization(id, notes)
      showToast(`Report filed for ${orgName}.`, "success"); load()
    } catch (err) { showToast(errorMessage(err), "error") }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="grid gap-6">
      {toast && (
        <div className={["fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl px-4 py-3 shadow-panel text-sm font-semibold", toast.tone === "success" ? "bg-moss text-paper" : "bg-warn text-paper"].join(" ")}>
          {toast.msg}
          <button onClick={() => setToast(null)}><X size={14} /></button>
        </div>
      )}

      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-ink">Organizations</h1>
          <p className="mt-1 text-sm text-neutral-600">Tenant directory, domains, and operational lifecycle.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" type="button" onClick={load} disabled={loading}>
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          </Button>
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus size={16} />New organization
          </Button>
        </div>
      </header>

      {/* status breakdown pills */}
      {Object.keys(statusCounts).length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => { setStatusFilter(""); setPage(1) }}
            className={["rounded-full border px-3 py-1 text-xs font-bold transition", !statusFilter ? "border-ink bg-ink text-paper" : "border-line bg-white text-neutral-600 hover:border-ink"].join(" ")}
          >
            All · {total}
          </button>
          {(STATUS_OPTIONS.slice(1) as string[]).map((s) => (
            statusCounts[s] !== undefined && (
              <button key={s}
                onClick={() => { setStatusFilter(s); setPage(1) }}
                className={["inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold transition", statusFilter === s ? "border-ink bg-ink text-paper" : ["border", STATUS_STYLE[s]].join(" ") + " hover:border-ink"].join(" ")}
              >
                {STATUS_ICON[s]}
                {s.charAt(0).toUpperCase() + s.slice(1)} · {statusCounts[s]}
              </button>
            )
          ))}
        </div>
      )}

      {/* search */}
      <div className="flex flex-wrap gap-3 rounded-2xl border border-line bg-white p-4 shadow-panel md:items-end">
        <Field label="Status">
          <Select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}>
            {STATUS_OPTIONS.map((s) => (
              <option key={s || "any"} value={s}>{s ? s.charAt(0).toUpperCase() + s.slice(1) : "Any status"}</option>
            ))}
          </Select>
        </Field>
        <Field label="Search">
          <div className="flex gap-2">
            <Input placeholder="Name or domain" value={searchDraft} onChange={(e) => setSearchDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && applySearch()} />
            <Button type="button" variant="secondary" onClick={applySearch}><Search size={16} /></Button>
          </div>
        </Field>
        {hasFilters && (
          <button onClick={clearFilters} className="flex h-10 items-center gap-1.5 rounded-md border border-line px-3 text-sm font-semibold text-neutral-600 hover:border-ink hover:text-ink">
            <X size={14} /> Clear
          </button>
        )}
      </div>

      {/* table */}
      <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-panel">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-line bg-paper">
              <tr>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">Organization</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">Domain</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">Status</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">Members</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">Last activity</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-neutral-500">
                    {hasFilters ? "No organizations match your filters." : "No organizations yet."}
                  </td>
                </tr>
              )}
              {items.map((org) => (
                <tr key={org.id} className="border-t border-line transition-colors hover:bg-paper/60">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-xs font-bold text-paper"
                        style={{ backgroundColor: orgColor(org.name) }}
                      >
                        {orgInitials(org.name)}
                      </div>
                      <div>
                        <Link to={`/admin/organizations/${org.id}`} className="flex items-center gap-1 font-semibold text-ink hover:text-signal hover:underline">
                          {org.name}
                          <ChevronRight size={12} className="text-neutral-400" />
                        </Link>
                        <div className="text-xs text-neutral-500">Created {timeAgo(org.created_at)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-neutral-600">{org.domain}</td>
                  <td className="px-4 py-3">
                    <span className={["inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-bold", STATUS_STYLE[org.status] ?? "bg-paper text-ink border-line"].join(" ")}>
                      {STATUS_ICON[org.status]}
                      {org.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="tabular-nums font-semibold text-ink">{org.active_members}</span>
                    <span className="text-xs text-neutral-500"> active</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-500">{timeAgo(org.created_at)}</td>
                  <td className="px-4 py-3">
                    <OrgRowActions org={org} onAction={inlineAction} onReport={inlineReport} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex flex-col items-center justify-between gap-3 border-t border-line px-4 py-3 text-sm sm:flex-row">
          <span className="text-neutral-600">
            {total === 0 ? "No organizations" : `Showing ${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} of ${total}`}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="secondary" type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <span className="tabular-nums text-neutral-600">{page} / {totalPages}</span>
            <Button variant="secondary" type="button" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </div>
      </div>

      {/* create modal */}
      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-4 sm:items-center">
          <div className="w-full max-w-md rounded-2xl border border-line bg-paper p-6 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-ink text-paper">
                <Building2 size={18} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-ink">Create organization</h2>
                <p className="text-xs text-neutral-500">New tenant on the platform</p>
              </div>
            </div>
            <div className="mt-5 grid gap-4">
              <Field label="Display name">
                <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Acme Clinics" />
              </Field>
              <Field label="Domain key (must be unique)">
                <Input value={newDomain} onChange={(e) => setNewDomain(e.target.value)} placeholder="acme.example.com" />
              </Field>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button type="button" disabled={!newName.trim() || !newDomain.trim()} onClick={submitCreate}>Create</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function OrgRowActions({ org, onAction, onReport }: {
  org: OrganizationListItem
  onAction: (id: string, action: "activate" | "deactivate" | "suspend" | "abort", name: string) => void
  onReport: (id: string, notes: string, name: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [reportMode, setReportMode] = useState(false)
  const [reportNotes, setReportNotes] = useState("")
  const [confirmAbort, setConfirmAbort] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function h(e: MouseEvent) { if (ref.current && !ref.current.contains(e.target as Node)) { setOpen(false); setReportMode(false); setConfirmAbort(false) } }
    document.addEventListener("mousedown", h)
    return () => document.removeEventListener("mousedown", h)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-lg border border-line text-neutral-500 hover:border-ink hover:text-ink transition">
        <MoreHorizontal size={16} />
      </button>

      {open && !reportMode && !confirmAbort && (
        <div className="absolute right-0 top-full z-40 mt-1 w-52 overflow-hidden rounded-xl border border-line bg-white py-1 shadow-panel">
          <Link to={`/admin/organizations/${org.id}`} onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm font-semibold text-ink hover:bg-paper">
            <ChevronRight size={14} /> View details
          </Link>
          <div className="my-1 border-t border-line" />
          {org.status !== "active" && (
            <button onClick={() => { onAction(org.id, "activate", org.name); setOpen(false) }}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-semibold text-moss hover:bg-paper">
              <CheckCircle size={14} /> Activate
            </button>
          )}
          {org.status === "active" && (
            <button onClick={() => { onAction(org.id, "deactivate", org.name); setOpen(false) }}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-semibold text-neutral-700 hover:bg-paper">
              Deactivate
            </button>
          )}
          {org.status !== "suspended" && org.status !== "aborted" && (
            <button onClick={() => { onAction(org.id, "suspend", org.name); setOpen(false) }}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-semibold text-amber-700 hover:bg-paper">
              <AlertTriangle size={14} /> Suspend
            </button>
          )}
          <button onClick={() => setReportMode(true)}
            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-semibold text-neutral-700 hover:bg-paper">
            Report / flag
          </button>
          <div className="my-1 border-t border-line" />
          {org.status !== "aborted" && (
            <button onClick={() => setConfirmAbort(true)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-semibold text-warn hover:bg-paper">
              <XCircle size={14} /> Abort
            </button>
          )}
        </div>
      )}

      {open && reportMode && (
        <div className="absolute right-0 top-full z-40 mt-1 w-72 overflow-hidden rounded-xl border border-line bg-white p-4 shadow-panel">
          <p className="text-sm font-bold text-ink">File report for {org.name}</p>
          <Textarea className="mt-2 w-full" rows={3} value={reportNotes} onChange={(e) => setReportNotes(e.target.value)} placeholder="Describe the issue…" />
          <div className="mt-3 flex justify-end gap-2">
            <button onClick={() => setReportMode(false)} className="text-sm text-neutral-500 hover:text-ink">Cancel</button>
            <Button type="button" disabled={!reportNotes.trim()} onClick={() => { onReport(org.id, reportNotes, org.name); setOpen(false); setReportMode(false); setReportNotes("") }}>Submit</Button>
          </div>
        </div>
      )}

      {open && confirmAbort && (
        <div className="absolute right-0 top-full z-40 mt-1 w-64 overflow-hidden rounded-xl border border-warn/30 bg-white p-4 shadow-panel">
          <p className="text-sm font-bold text-warn">Abort {org.name}?</p>
          <p className="mt-1 text-xs text-neutral-600">This marks the organization as aborted. This action cannot be undone easily.</p>
          <div className="mt-3 flex gap-2">
            <Button variant="ghost" type="button" onClick={() => setConfirmAbort(false)}>Cancel</Button>
            <Button variant="danger" type="button" onClick={() => { onAction(org.id, "abort", org.name); setOpen(false); setConfirmAbort(false) }}>Abort</Button>
          </div>
        </div>
      )}
    </div>
  )
}
