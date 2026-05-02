import { api } from "./client"
import type { AppointmentTypeDetail, AppointmentTypeListItem, Paginated, Resource } from "./types"

export async function listAppointmentTypes(published: boolean | null = true): Promise<Paginated<AppointmentTypeListItem>> {
  const params = published === null ? {} : { published }
  const res = await api.get<Paginated<AppointmentTypeListItem>>("/appointment-types", { params })
  return res.data
}

export async function getAppointmentType(id: string): Promise<AppointmentTypeDetail> {
  const res = await api.get<AppointmentTypeDetail>(`/appointment-types/${id}`)
  return res.data
}

export async function getAppointmentTypeByShare(token: string): Promise<AppointmentTypeDetail> {
  const res = await api.get<AppointmentTypeDetail>(`/appointment-types/share/${token}`)
  return res.data
}

export async function createAppointmentType(payload: {
  title: string
  preset_type?: string
  description?: string
  duration_minutes: number
  timezone: string
  resource_type: string
  future_days_limit?: number
  venue?: string
}) {
  const res = await api.post<AppointmentTypeDetail>("/appointment-types", payload)
  return res.data
}

export async function updateAppointmentType(
  appointmentTypeId: string,
  payload: {
    title: string
    preset_type?: string
    description?: string
    duration_minutes: number
    timezone: string
    resource_type: string
    future_days_limit?: number
    venue?: string
    confirmation_msg?: string
  },
) {
  const res = await api.patch<AppointmentTypeDetail>(`/appointment-types/${appointmentTypeId}`, payload)
  return res.data
}

export async function addResource(appointmentTypeId: string, payload: { name: string; capacity: number; resource_type: string }) {
  const res = await api.post<Resource>(`/appointment-types/${appointmentTypeId}/resources`, payload)
  return res.data
}

export async function replaceResources(appointmentTypeId: string, payload: Array<{ name: string; capacity: number; resource_type: string }>) {
  const res = await api.put<Resource[]>(`/appointment-types/${appointmentTypeId}/resources`, payload)
  return res.data
}

export async function replaceWorkingHours(
  appointmentTypeId: string,
  payload: Array<{ day_of_week: number; start_time: string; end_time: string }>,
) {
  const res = await api.post(`/appointment-types/${appointmentTypeId}/working-hours`, payload)
  return res.data as { count: number }
}

export async function replaceQuestions(
  appointmentTypeId: string,
  payload: Array<{ label: string; question_type: string; required: boolean; options?: string[] }>,
) {
  const res = await api.post(`/appointment-types/${appointmentTypeId}/questions`, payload)
  return res.data as { count: number }
}

export async function updateRules(appointmentTypeId: string, payload: Record<string, unknown>) {
  const res = await api.post<AppointmentTypeDetail>(`/appointment-types/${appointmentTypeId}/booking-rules`, payload)
  return res.data
}

export async function publishAppointmentType(appointmentTypeId: string) {
  const res = await api.patch(`/appointment-types/${appointmentTypeId}/publish`)
  return res.data as { id: string; is_published: boolean; slots_generated: number }
}

export async function shareLink(appointmentTypeId: string) {
  const res = await api.get<{ url: string }>(`/appointment-types/${appointmentTypeId}/share-link`)
  return res.data
}
