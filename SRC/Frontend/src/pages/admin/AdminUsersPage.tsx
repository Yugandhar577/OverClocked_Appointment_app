import {
  BadgeCheck,
  ChevronDown,
  MoreHorizontal,
  Power,
  RefreshCw,
  Search,
  Shield,
  ShieldCheck,
  UserCheck,
  UserMinus,
  UserPlus,
  X,
} from "lucide-react"
import type { ReactNode } from "react"
import { useCallback, useEffect, useRef, useState } from "react"

import { activateUser, deactivateUser, listUsers, updateUserRoles } from "../../api/admin"
import type { ListUsersParams } from "../../api/admin"
import { errorMessage } from "../../api/client"
import { listOrganizations } from "../../api/organizations"
import type { AdminUser } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Field, Input, Select } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const ROLE_OPTIONS = ["customer", "organiser", "admin"] as const

const ROLE_STYLE: Record<string, string> = {
  customer: "bg-blue-50 text-blue-800",
  organiser: "bg-emerald-50 text-emerald-800",
  admin: "bg-primary text-paper",
}

function initials(name: string) {
  return name.split(" ").slice(0, 2).map((p) => p[0]?.toUpperCase() ?? "").join("")
}

function avatarColor(name: string) {
  const colors = ["#275efe", "#44624a", "#a5533d", "#6d28d9", "#0369a1", "#b45309"]
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffffff
  return colors[Math.abs(hash) % colors.length]
}

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (diff === 0) return "today"
  if (diff === 1) return "yesterday"
  if (diff < 30) return `${diff}d ago`
  if (diff < 365) return `${Math.floor(diff / 30)}mo ago`
  return `${Math.floor(diff / 365)}y ago`
}

export function AdminUsersPage() {
  const [items, setItems] = useState<AdminUser[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [roleFilter, setRoleFilter] = useState("")
  const [activeFilter, setActiveFilter] = useState<string>("")
  const [searchDraft, setSearchDraft] = useState("")
  const [searchApplied, setSearchApplied] = useState("")
  const [toast, setToast] = useState<{ msg: string; tone: "success" | "error" } | null>(null)
  const [roleModalUser, setRoleModalUser] = useState<AdminUser | null>(null)
  const [draftRoles, setDraftRoles] = useState<Set<string>>(new Set())
  const [orgMap, setOrgMap] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  // summary counts (derived from full unfiltered store — fetched once)
  const [allStats, setAllStats] = useState({ total: 0, active: 0, inactive: 0, unverified: 0 })

  useEffect(() => {
    listUsers({ page: 1, page_size: 1000 }).then((d) => {
      const all = d.items
      setAllStats({
        total: d.total,
        active: all.filter((u) => u.is_active).length,
        inactive: all.filter((u) => !u.is_active).length,
        unverified: all.filter((u) => !u.is_verified).length,
      })
    }).catch(() => {})
  }, [])

  useEffect(() => {
    listOrganizations({ page: 1, page_size: 200 }).then((d) => {
      const map: Record<string, string> = {}
      for (const o of d.items) map[o.id] = o.name
      setOrgMap(map)
    }).catch(() => {})
  }, [])

  const buildParams = useCallback((): ListUsersParams => {
    const p: ListUsersParams = { page, page_size: pageSize }
    if (roleFilter) p.role = roleFilter
    if (activeFilter === "true") p.is_active = true
    if (activeFilter === "false") p.is_active = false
    if (searchApplied.trim()) p.search = searchApplied.trim()
    return p
  }, [page, pageSize, roleFilter, activeFilter, searchApplied])

  const load = useCallback(() => {
    setLoading(true)
    listUsers(buildParams())
      .then((data) => {
        setItems(data.items)
        setTotal(data.total)
      })
      .catch((err) => showToast(errorMessage(err), "error"))
      .finally(() => setLoading(false))
  }, [buildParams])

  useEffect(() => { load() }, [load])

  function showToast(msg: string, tone: "success" | "error") {
    setToast({ msg, tone })
    setTimeout(() => setToast(null), 3500)
  }

  function applySearch() {
    setPage(1)
    setSearchApplied(searchDraft)
  }

  async function toggle(user: AdminUser) {
    try {
      if (user.is_active) await deactivateUser(user.id)
      else await activateUser(user.id)
      showToast(`${user.full_name} ${user.is_active ? "deactivated" : "activated"}.`, "success")
      load()
    } catch (err) { showToast(errorMessage(err), "error") }
  }

  async function quickAddOrganiser(user: AdminUser) {
    try {
      await updateUserRoles(user.id, Array.from(new Set([...user.roles, "organiser"])))
      showToast(`${user.full_name} promoted to organiser.`, "success")
      load()
    } catch (err) { showToast(errorMessage(err), "error") }
  }

  function openRoleModal(user: AdminUser) {
    setRoleModalUser(user)
    setDraftRoles(new Set(user.roles))
  }

  async function saveRoles() {
    if (!roleModalUser) return
    if (draftRoles.size === 0) { showToast("Select at least one role.", "error"); return }
    try {
      await updateUserRoles(roleModalUser.id, Array.from(draftRoles))
      setRoleModalUser(null)
      showToast("Roles updated.", "success")
      load()
    } catch (err) { showToast(errorMessage(err), "error") }
  }

  function clearFilters() {
    setRoleFilter("")
    setActiveFilter("")
    setSearchDraft("")
    setSearchApplied("")
    setPage(1)
  }

  const hasFilters = roleFilter || activeFilter || searchApplied
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="grid gap-6">
      {/* toast */}
      {toast && (
        <div className={[
          "fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl px-4 py-3 shadow-panel text-sm font-semibold",
          toast.tone === "success" ? "bg-moss text-paper" : "bg-warn text-paper",
        ].join(" ")}>
          {toast.msg}
          <button onClick={() => setToast(null)}><X size={14} /></button>
        </div>
      )}

      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-ink">Users &amp; providers</h1>
          <p className="mt-1 text-sm text-neutral-600">Search, filter, activate, and manage role assignments.</p>
        </div>
        <Button variant="secondary" type="button" onClick={load} disabled={loading}>
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          Refresh
        </Button>
      </header>

      {/* stats bar */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatChip label="Total" value={allStats.total} color="text-ink" />
        <StatChip label="Active" value={allStats.active} color="text-moss" />
        <StatChip label="Inactive" value={allStats.inactive} color="text-warn" />
        <StatChip label="Unverified" value={allStats.unverified} color="text-clay" />
      </div>

      {/* filters */}
      <div className="flex flex-col gap-3 rounded-2xl border border-line bg-white p-4 shadow-panel md:flex-row md:flex-wrap md:items-end">
        <Field label="Role">
          <Select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1) }}>
            <option value="">All roles</option>
            <option value="customer">Customer</option>
            <option value="organiser">Organiser</option>
            <option value="admin">Admin</option>
          </Select>
        </Field>
        <Field label="Status">
          <Select value={activeFilter} onChange={(e) => { setActiveFilter(e.target.value); setPage(1) }}>
            <option value="">Any</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </Select>
        </Field>
        <Field label="Search">
          <div className="flex gap-2">
            <Input placeholder="Name or email" value={searchDraft} onChange={(e) => setSearchDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && applySearch()} />
            <Button type="button" variant="secondary" onClick={applySearch} title="Search"><Search size={16} /></Button>
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
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-line bg-paper">
              <tr>
                <Th>User</Th>
                <Th>Roles</Th>
                <Th>Organization</Th>
                <Th>Status</Th>
                <Th>Joined</Th>
                <Th>Actions</Th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-neutral-500">
                    No users match your filters.
                  </td>
                </tr>
              )}
              {items.map((user) => (
                <tr key={user.id} className="border-t border-line transition-colors hover:bg-paper/60">
                  <Td>
                    <div className="flex items-center gap-3">
                      <div
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-bold text-paper"
                        style={{ backgroundColor: avatarColor(user.full_name) }}
                      >
                        {initials(user.full_name)}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5 font-semibold text-ink">
                          {user.full_name}
                          {user.is_verified && <span title="Verified"><BadgeCheck size={13} className="text-signal" /></span>}
                        </div>
                        <div className="text-xs text-neutral-500">{user.email}</div>
                      </div>
                    </div>
                  </Td>
                  <Td>
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map((r) => (
                        <span key={r} className={["rounded-full px-2 py-0.5 text-xs font-bold", ROLE_STYLE[r] ?? "bg-paper text-ink"].join(" ")}>
                          {r}
                        </span>
                      ))}
                    </div>
                  </Td>
                  <Td>
                    {user.organization_id && orgMap[user.organization_id] ? (
                      <span className="rounded-md bg-paper px-2 py-0.5 text-xs font-semibold text-neutral-700">
                        {orgMap[user.organization_id]}
                      </span>
                    ) : (
                      <span className="text-neutral-400">—</span>
                    )}
                  </Td>
                  <Td>
                    <div className="flex items-center gap-1.5">
                      <span className={["h-2 w-2 rounded-full", user.is_active ? "bg-moss" : "bg-warn"].join(" ")} />
                      <span className={user.is_active ? "text-moss font-semibold" : "text-warn font-semibold"}>
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </Td>
                  <Td>
                    <span className="text-xs text-neutral-500">{timeAgo(user.created_at)}</span>
                  </Td>
                  <Td>
                    <UserRowActions user={user} onToggle={toggle} onEditRoles={openRoleModal} onAddOrganiser={quickAddOrganiser} />
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* pagination */}
        <div className="flex flex-col items-center justify-between gap-3 border-t border-line px-4 py-3 text-sm sm:flex-row">
          <span className="text-neutral-600">
            {total === 0 ? "No users" : `Showing ${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} of ${total}`}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="secondary" type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <span className="tabular-nums text-neutral-600">{page} / {totalPages}</span>
            <Button variant="secondary" type="button" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </div>
      </div>

      {/* role modal */}
      {roleModalUser && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-4 sm:items-center" role="dialog">
          <div className="max-h-[90vh] w-full max-w-md overflow-auto rounded-2xl border border-line bg-paper p-6 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-full text-sm font-bold text-paper" style={{ backgroundColor: avatarColor(roleModalUser.full_name) }}>
                {initials(roleModalUser.full_name)}
              </div>
              <div>
                <h2 className="text-base font-bold text-ink">{roleModalUser.full_name}</h2>
                <p className="text-xs text-neutral-500">{roleModalUser.email}</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-neutral-600">Assign roles. At least one is required. Changes apply immediately.</p>
            <div className="mt-4 grid gap-2">
              {ROLE_OPTIONS.map((r) => (
                <label key={r} className={["flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 transition", draftRoles.has(r) ? "border-primary bg-primary text-paper" : "border-line bg-white text-ink hover:border-neutral-400"].join(" ")}>
                  <input type="checkbox" className="sr-only" checked={draftRoles.has(r)} onChange={() => {
                    setDraftRoles((prev) => { const next = new Set(prev); next.has(r) ? next.delete(r) : next.add(r); return next })
                  }} />
                  <span className="flex items-center gap-2 text-sm font-semibold capitalize">
                    {r === "admin" && <Shield size={14} />}
                    {r === "organiser" && <ShieldCheck size={14} />}
                    {r === "customer" && <UserCheck size={14} />}
                    {r}
                  </span>
                  {draftRoles.has(r) && <BadgeCheck size={14} className="ml-auto" />}
                </label>
              ))}
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={() => setRoleModalUser(null)}>Cancel</Button>
              <Button type="button" onClick={saveRoles} disabled={draftRoles.size === 0}>Save roles</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function UserRowActions({ user, onToggle, onEditRoles, onAddOrganiser }: {
  user: AdminUser
  onToggle: (u: AdminUser) => void
  onEditRoles: (u: AdminUser) => void
  onAddOrganiser: (u: AdminUser) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    function handler(e: MouseEvent) { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const items = [
    { label: "Edit roles", icon: <Shield size={14} />, onClick: () => { onEditRoles(user); setOpen(false) } },
    ...(!user.roles.includes("organiser") ? [{ label: "Promote to organiser", icon: <UserPlus size={14} />, onClick: () => { onAddOrganiser(user); setOpen(false) } }] : []),
    {
      label: user.is_active ? "Deactivate" : "Activate",
      icon: user.is_active ? <UserMinus size={14} /> : <Power size={14} />,
      onClick: () => { onToggle(user); setOpen(false) },
      danger: user.is_active,
    },
  ]

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-lg border border-line text-neutral-500 transition hover:border-ink hover:text-ink"
      >
        <MoreHorizontal size={16} />
      </button>
      {open && (
        <div className="absolute right-0 top-full z-40 mt-1 w-48 overflow-hidden rounded-xl border border-line bg-white py-1 shadow-panel">
          {items.map((item) => (
            <button key={item.label} onClick={item.onClick}
              className={["flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm font-semibold transition hover:bg-paper", item.danger ? "text-warn" : "text-ink"].join(" ")}>
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function StatChip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-xl border border-line bg-white px-4 py-3 shadow-panel">
      <div className="text-xs font-bold uppercase tracking-wider text-neutral-500">{label}</div>
      <div className={["mt-1 text-2xl font-bold tabular-nums", color].join(" ")}>{value}</div>
    </div>
  )
}

function Th({ children }: { children: ReactNode }) {
  return <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-neutral-500">{children}</th>
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-4 py-3 align-middle">{children}</td>
}

// unused but kept for import parity
function _ChevronDown() { return <ChevronDown size={0} /> }
void _ChevronDown
