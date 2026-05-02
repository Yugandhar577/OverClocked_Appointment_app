import { api } from "./client"

export type FeatureFlags = Record<string, boolean>

export interface ThemeSettings {
  id: string | null
  name: string
  settings: Record<string, string>
  is_default: boolean
}

export interface WaitlistEntry {
  id: string
  appointment_type_id: string
  slot_id: string | null
  customer_id: string
  status: string
  offer_mode: string
  priority: number
  expires_at: string | null
  created_at: string
}

export interface AnalyticsSummary {
  total_bookings: number
  completed_bookings: number
  cancelled_bookings: number
  no_shows: number
  waitlist_conversion_rate: number
  most_booked_services: { service: string; count: number }[]
  peak_booking_hours: { hour: string; count: number }[]
  staff_utilization: { staff: string; utilization: number }[]
}

export interface PackagePlan {
  id: string
  name: string
  appointment_type_id: string | null
  session_count: number
  price: string
  currency: string
  is_active: boolean
}

export async function getFeatureFlags() {
  const { data } = await api.get<{ flags: FeatureFlags }>("/features")
  return data.flags
}

export async function getTheme() {
  const { data } = await api.get<ThemeSettings>("/theme")
  return data
}

export async function saveTheme(payload: { name: string; settings: Record<string, string> }) {
  const { data } = await api.put<ThemeSettings>("/admin/theme", payload)
  return data
}

export async function resetTheme() {
  const { data } = await api.post<ThemeSettings>("/admin/theme/reset")
  return data
}

export async function listWaitlist() {
  const { data } = await api.get<WaitlistEntry[]>("/admin/waitlist")
  return data
}

export async function joinWaitlist(payload: { appointment_type_id: string; slot_id?: string; notes?: string }) {
  const { data } = await api.post<WaitlistEntry>("/waitlist", payload)
  return data
}

export async function getAnalytics() {
  const { data } = await api.get<AnalyticsSummary>("/admin/analytics")
  return data
}

export async function listPackages() {
  const { data } = await api.get<PackagePlan[]>("/packages")
  return data
}

export async function createPackage(payload: { name: string; session_count: number; price: number; currency: string }) {
  const { data } = await api.post<PackagePlan>("/admin/packages", payload)
  return data
}

export async function createManualBooking(payload: {
  customer_id: string
  appointment_type_id: string
  slot_id: string
  people_count: number
  resource_id?: string
  payment_status?: string
  internal_notes?: string
}) {
  const { data } = await api.post("/admin/manual-bookings", payload)
  return data
}
