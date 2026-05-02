import { api } from "./client"
import type { AdminUser, Paginated } from "./types"

export async function listUsers(): Promise<Paginated<AdminUser>> {
  const res = await api.get<Paginated<AdminUser>>("/admin/users")
  return res.data
}

export async function activateUser(id: string): Promise<AdminUser> {
  const res = await api.patch<AdminUser>(`/admin/users/${id}/activate`)
  return res.data
}

export async function deactivateUser(id: string): Promise<AdminUser> {
  const res = await api.patch<AdminUser>(`/admin/users/${id}/deactivate`)
  return res.data
}

export async function updateUserRoles(id: string, roles: string[]) {
  const res = await api.patch<{ roles: string[] }>(`/admin/users/${id}/roles`, { roles })
  return res.data
}

export async function adminStats() {
  const res = await api.get<{
    total_users: number
    total_organisers: number
    total_customers: number
    total_appointments: number
    appointments_by_status: Record<string, number>
  }>("/admin/stats")
  return res.data
}
