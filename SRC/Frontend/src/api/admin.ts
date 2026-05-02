import {
  MOCK_ENABLED,
  mockActivateUser,
  mockAdminStats,
  mockDeactivateUser,
  mockListUsers,
  mockUpdateUserRoles,
} from "../lib/adminMockData"
import { api } from "./client"
import type { AdminUser, Paginated } from "./types"

export type ListUsersParams = {
  page?: number
  page_size?: number
  role?: string
  is_active?: boolean
  search?: string
}

export async function listUsers(params?: ListUsersParams): Promise<Paginated<AdminUser>> {
  if (MOCK_ENABLED) return mockListUsers(params)
  const res = await api.get<Paginated<AdminUser>>("/admin/users", { params })
  return res.data
}

export async function activateUser(id: string): Promise<AdminUser> {
  if (MOCK_ENABLED) return mockActivateUser(id)
  const res = await api.patch<AdminUser>(`/admin/users/${id}/activate`)
  return res.data
}

export async function deactivateUser(id: string): Promise<AdminUser> {
  if (MOCK_ENABLED) return mockDeactivateUser(id)
  const res = await api.patch<AdminUser>(`/admin/users/${id}/deactivate`)
  return res.data
}

export async function updateUserRoles(id: string, roles: string[]) {
  if (MOCK_ENABLED) return mockUpdateUserRoles(id, roles)
  const res = await api.patch<{ roles: string[] }>(`/admin/users/${id}/roles`, { roles })
  return res.data
}

export async function adminStats() {
  if (MOCK_ENABLED) return mockAdminStats()
  const res = await api.get<{
    total_users: number
    total_organisers: number
    total_customers: number
    total_appointments: number
    appointments_by_status: Record<string, number>
  }>("/admin/stats")
  return res.data
}
