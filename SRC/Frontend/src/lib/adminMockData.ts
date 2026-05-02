/**
 * Synthetic admin data used when VITE_ADMIN_MOCK_DATA=true.
 * All mutations are in-memory — resets on page reload, which is fine for demo.
 */

import type { AdminUser, OrganizationDetail, OrganizationListItem, Paginated } from "../api/types"

// ─── helpers ──────────────────────────────────────────────────────────────────

function uuid(n: number) {
  return `00000000-0000-0000-0000-${String(n).padStart(12, "0")}`
}

function iso(daysAgo: number) {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  return d.toISOString()
}

function delay<T>(ms: number, value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

// ─── organizations store ──────────────────────────────────────────────────────

const ORG_SEED: OrganizationDetail[] = [
  {
    id: uuid(1),
    name: "Acme Clinics",
    domain: "acme.demo",
    status: "active",
    active_members: 14,
    total_members: 18,
    active_instances: 5,
    admin_report_notes: null,
    created_at: iso(120),
    updated_at: iso(3),
  },
  {
    id: uuid(2),
    name: "Beta Labs",
    domain: "beta.demo",
    status: "active",
    active_members: 6,
    total_members: 9,
    active_instances: 2,
    admin_report_notes: null,
    created_at: iso(90),
    updated_at: iso(10),
  },
  {
    id: uuid(3),
    name: "Gamma Health",
    domain: "gamma.health",
    status: "active",
    active_members: 22,
    total_members: 25,
    active_instances: 8,
    admin_report_notes: null,
    created_at: iso(60),
    updated_at: iso(1),
  },
  {
    id: uuid(4),
    name: "Delta Physio",
    domain: "delta.physio",
    status: "inactive",
    active_members: 0,
    total_members: 4,
    active_instances: 0,
    admin_report_notes: "Suspended for non-payment of subscription.",
    created_at: iso(200),
    updated_at: iso(30),
  },
  {
    id: uuid(5),
    name: "Epsilon Dental",
    domain: "epsilon.dental",
    status: "flagged",
    active_members: 3,
    total_members: 5,
    active_instances: 1,
    admin_report_notes: "Multiple complaint tickets filed. Under review.",
    created_at: iso(75),
    updated_at: iso(5),
  },
  {
    id: uuid(6),
    name: "Zeta Wellness",
    domain: "zeta.wellness",
    status: "suspended",
    active_members: 0,
    total_members: 7,
    active_instances: 0,
    admin_report_notes: "Breach of terms of service detected on 2026-04-12.",
    created_at: iso(45),
    updated_at: iso(20),
  },
  {
    id: uuid(7),
    name: "Eta Physiotherapy",
    domain: "eta.physio",
    status: "active",
    active_members: 9,
    total_members: 11,
    active_instances: 3,
    admin_report_notes: null,
    created_at: iso(30),
    updated_at: iso(2),
  },
  {
    id: uuid(8),
    name: "Theta Sports Med",
    domain: "theta.sports",
    status: "aborted",
    active_members: 0,
    total_members: 2,
    active_instances: 0,
    admin_report_notes: "Org aborted by admin after fraudulent activity was confirmed.",
    created_at: iso(180),
    updated_at: iso(60),
  },
]

// Deep-clone so mutations don't affect the seed
const orgStore: OrganizationDetail[] = ORG_SEED.map((o) => ({ ...o }))

// ─── users store ─────────────────────────────────────────────────────────────

const USER_SEED: AdminUser[] = [
  { id: uuid(101), full_name: "Admin User", email: "admin@test.local", roles: ["admin"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(200), organization_id: null },
  { id: uuid(102), full_name: "Organiser One", email: "org1@test.local", roles: ["organiser"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: "+91-9000000001", created_at: iso(180), organization_id: uuid(1) },
  { id: uuid(103), full_name: "Organiser Two", email: "org2@test.local", roles: ["organiser"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: "+91-9000000002", created_at: iso(170), organization_id: uuid(2) },
  { id: uuid(104), full_name: "Customer 1", email: "cust1@test.local", roles: ["customer"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(160), organization_id: null },
  { id: uuid(105), full_name: "Customer 2", email: "cust2@test.local", roles: ["customer"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(155), organization_id: null },
  { id: uuid(106), full_name: "Customer 3", email: "cust3@test.local", roles: ["customer"], is_verified: false, is_active: true, timezone: "UTC", phone: null, created_at: iso(140), organization_id: null },
  { id: uuid(107), full_name: "Customer 4", email: "cust4@test.local", roles: ["customer"], is_verified: true, is_active: false, timezone: "UTC", phone: null, created_at: iso(130), organization_id: null },
  { id: uuid(108), full_name: "Customer 5", email: "cust5@test.local", roles: ["customer", "organiser"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(120), organization_id: uuid(1) },
  { id: uuid(109), full_name: "Dr. Ramesh Sharma", email: "ramesh@acme.demo", roles: ["organiser"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: "+91-9800000001", created_at: iso(100), organization_id: uuid(1) },
  { id: uuid(110), full_name: "Priya Nair", email: "priya@gamma.health", roles: ["organiser"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: "+91-9800000002", created_at: iso(95), organization_id: uuid(3) },
  { id: uuid(111), full_name: "Arjun Mehta", email: "arjun@gamma.health", roles: ["customer"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(90), organization_id: uuid(3) },
  { id: uuid(112), full_name: "Sneha Patil", email: "sneha@beta.demo", roles: ["customer"], is_verified: true, is_active: false, timezone: "UTC", phone: null, created_at: iso(80), organization_id: uuid(2) },
  { id: uuid(113), full_name: "Vikram Singh", email: "vikram@eta.physio", roles: ["organiser"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: "+91-9700000001", created_at: iso(70), organization_id: uuid(7) },
  { id: uuid(114), full_name: "Anjali Desai", email: "anjali@zeta.wellness", roles: ["organiser"], is_verified: true, is_active: false, timezone: "Asia/Kolkata", phone: null, created_at: iso(65), organization_id: uuid(6) },
  { id: uuid(115), full_name: "Ravi Kumar", email: "ravi@test.local", roles: ["customer"], is_verified: false, is_active: true, timezone: "UTC", phone: null, created_at: iso(50), organization_id: null },
  { id: uuid(116), full_name: "Meera Iyer", email: "meera@test.local", roles: ["customer"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(45), organization_id: null },
  { id: uuid(117), full_name: "Suresh Babu", email: "suresh@acme.demo", roles: ["organiser", "customer"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: "+91-9600000001", created_at: iso(40), organization_id: uuid(1) },
  { id: uuid(118), full_name: "Nandini Roy", email: "nandini@test.local", roles: ["customer"], is_verified: true, is_active: true, timezone: "UTC", phone: null, created_at: iso(30), organization_id: null },
  { id: uuid(119), full_name: "Kapil Dev", email: "kapil@theta.sports", roles: ["organiser"], is_verified: true, is_active: false, timezone: "Asia/Kolkata", phone: null, created_at: iso(20), organization_id: uuid(8) },
  { id: uuid(120), full_name: "Lalitha Menon", email: "lalitha@gamma.health", roles: ["customer"], is_verified: true, is_active: true, timezone: "Asia/Kolkata", phone: null, created_at: iso(10), organization_id: uuid(3) },
]

const userStore: AdminUser[] = USER_SEED.map((u) => ({ ...u }))

// ─── mock API functions ───────────────────────────────────────────────────────

type ListUsersParams = {
  page?: number
  page_size?: number
  role?: string
  is_active?: boolean
  search?: string
}

export async function mockListUsers(params?: ListUsersParams): Promise<Paginated<AdminUser>> {
  const { page = 1, page_size = 20, role, is_active, search } = params ?? {}
  let filtered = [...userStore]
  if (role) filtered = filtered.filter((u) => u.roles.includes(role))
  if (is_active !== undefined) filtered = filtered.filter((u) => u.is_active === is_active)
  if (search) {
    const q = search.toLowerCase()
    filtered = filtered.filter((u) => u.email.toLowerCase().includes(q) || u.full_name.toLowerCase().includes(q))
  }
  const total = filtered.length
  const items = filtered.slice((page - 1) * page_size, page * page_size)
  return delay(160, { items, total, page, page_size })
}

export async function mockActivateUser(id: string): Promise<AdminUser> {
  const u = userStore.find((x) => x.id === id)
  if (!u) throw new Error("User not found")
  u.is_active = true
  return delay(120, { ...u })
}

export async function mockDeactivateUser(id: string): Promise<AdminUser> {
  const u = userStore.find((x) => x.id === id)
  if (!u) throw new Error("User not found")
  u.is_active = false
  return delay(120, { ...u })
}

export async function mockUpdateUserRoles(id: string, roles: string[]): Promise<{ roles: string[] }> {
  const u = userStore.find((x) => x.id === id)
  if (!u) throw new Error("User not found")
  u.roles = roles
  return delay(120, { roles })
}

export async function mockAdminStats() {
  const total_users = userStore.length
  const total_organisers = userStore.filter((u) => u.roles.includes("organiser")).length
  const total_customers = userStore.filter((u) => u.roles.includes("customer")).length
  const total_appointments = 42
  return delay(200, {
    total_users,
    total_organisers,
    total_customers,
    total_appointments,
    appointments_by_status: {
      confirmed: 18,
      pending: 9,
      completed: 12,
      cancelled: 3,
    } as Record<string, number>,
  })
}

type ListOrgsParams = {
  page?: number
  page_size?: number
  status?: string
  search?: string
}

export async function mockListOrganizations(params?: ListOrgsParams): Promise<Paginated<OrganizationListItem>> {
  const { page = 1, page_size = 20, status, search } = params ?? {}
  let filtered = [...orgStore]
  if (status) filtered = filtered.filter((o) => o.status === status)
  if (search) {
    const q = search.toLowerCase()
    filtered = filtered.filter((o) => o.name.toLowerCase().includes(q) || o.domain.toLowerCase().includes(q))
  }
  const total = filtered.length
  const items: OrganizationListItem[] = filtered
    .slice((page - 1) * page_size, page * page_size)
    .map(({ id, name, domain, status, active_members, created_at }) => ({
      id,
      name,
      domain,
      status,
      active_members,
      created_at,
    }))
  return delay(160, { items, total, page, page_size })
}

export async function mockGetOrganization(id: string): Promise<OrganizationDetail> {
  const o = orgStore.find((x) => x.id === id)
  if (!o) throw new Error("Organization not found")
  return delay(140, { ...o })
}

export async function mockCreateOrganization(body: { name: string; domain: string }): Promise<OrganizationDetail> {
  const existing = orgStore.find((o) => o.domain === body.domain.trim().toLowerCase())
  if (existing) throw new Error("organization_domain_exists")
  const now = new Date().toISOString()
  const next: OrganizationDetail = {
    id: uuid(900 + orgStore.length),
    name: body.name.trim(),
    domain: body.domain.trim().toLowerCase(),
    status: "active",
    active_members: 0,
    total_members: 0,
    active_instances: 0,
    admin_report_notes: null,
    created_at: now,
    updated_at: now,
  }
  orgStore.unshift(next)
  return delay(200, { ...next })
}

export async function mockPatchOrganization(id: string, body: { name?: string; domain?: string }): Promise<OrganizationDetail> {
  const o = orgStore.find((x) => x.id === id)
  if (!o) throw new Error("Organization not found")
  if (body.name) o.name = body.name.trim()
  if (body.domain) {
    const d = body.domain.trim().toLowerCase()
    if (orgStore.some((x) => x.id !== id && x.domain === d)) throw new Error("organization_domain_exists")
    o.domain = d
  }
  o.updated_at = new Date().toISOString()
  return delay(160, { ...o })
}

function setOrgStatus(id: string, status: string, notes?: string): Promise<OrganizationDetail> {
  const o = orgStore.find((x) => x.id === id)
  if (!o) throw new Error("Organization not found")
  o.status = status
  if (notes) {
    const prev = o.admin_report_notes
    o.admin_report_notes = prev ? `${prev.trimEnd()}\n---\n${notes}` : notes
  }
  o.updated_at = new Date().toISOString()
  return delay(160, { ...o })
}

export const mockActivateOrganization = (id: string) => setOrgStatus(id, "active")
export const mockDeactivateOrganization = (id: string) => setOrgStatus(id, "inactive")
export const mockSuspendOrganization = (id: string) => setOrgStatus(id, "suspended")
export const mockAbortOrganization = (id: string) => setOrgStatus(id, "aborted")

export async function mockReportOrganization(id: string, notes: string): Promise<OrganizationDetail> {
  return setOrgStatus(id, "flagged", notes.trim())
}

// ─── sync helpers (no API round-trip needed) ──────────────────────────────────

export function getOrgName(id: string | null | undefined): string | null {
  if (!id) return null
  return orgStore.find((o) => o.id === id)?.name ?? null
}

export function getOrgStatusBreakdown(): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const o of orgStore) counts[o.status] = (counts[o.status] ?? 0) + 1
  return counts
}

export async function mockGetOrgMembers(orgId: string): Promise<AdminUser[]> {
  return delay(140, userStore.filter((u) => u.organization_id === orgId).map((u) => ({ ...u })))
}

export interface ActivityEvent {
  id: string
  type: "user_joined" | "org_created" | "org_flagged" | "user_deactivated" | "role_changed" | "booking_made"
  summary: string
  timestamp: string
}

export async function mockGetRecentActivity(): Promise<ActivityEvent[]> {
  return delay(120, [
    { id: "act1", type: "org_flagged", summary: "Epsilon Dental flagged for review", timestamp: iso(0) },
    { id: "act2", type: "user_joined", summary: "Lalitha Menon joined Gamma Health", timestamp: iso(0) },
    { id: "act3", type: "booking_made", summary: "42nd booking confirmed via Strategy Session", timestamp: iso(1) },
    { id: "act4", type: "role_changed", summary: "Customer 5 promoted to Organiser", timestamp: iso(1) },
    { id: "act5", type: "org_created", summary: "Eta Physiotherapy org created", timestamp: iso(2) },
    { id: "act6", type: "user_deactivated", summary: "Anjali Desai account deactivated", timestamp: iso(3) },
    { id: "act7", type: "booking_made", summary: "Dr. Ramesh Sharma slot confirmed", timestamp: iso(3) },
    { id: "act8", type: "user_joined", summary: "Ravi Kumar registered", timestamp: iso(4) },
  ])
}

// ─── flag ─────────────────────────────────────────────────────────────────────

export const MOCK_ENABLED = import.meta.env.VITE_ADMIN_MOCK_DATA === "true"
