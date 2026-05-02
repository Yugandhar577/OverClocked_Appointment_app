import { api } from "./client"
import type { ActivityItem, AppointmentTypeDetail, AppointmentTypeListItem, Paginated, Resource, ResourceCandidate } from "./types"

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
  image_url?: string
  video_url?: string
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
    image_url?: string
    video_url?: string
    booking_email_template?: string
    cancellation_email_template?: string
    reminder_email_hours?: number | null
    reminder_sms_hours?: number | null
  },
) {
  const res = await api.patch<AppointmentTypeDetail>(`/appointment-types/${appointmentTypeId}`, payload)
  return res.data
}

export async function resourceCandidates(mode: "user" | "resource"): Promise<ResourceCandidate[]> {
  const res = await api.get<ResourceCandidate[]>("/appointment-types/configure/resource-candidates", { params: { mode } })
  return res.data
}

export async function addResource(appointmentTypeId: string, payload: { name: string; capacity: number; resource_type: string; user_ref_id?: string | null }) {
  const res = await api.post<Resource>(`/appointment-types/${appointmentTypeId}/resources`, payload)
  return res.data
}

export async function replaceResources(
  appointmentTypeId: string,
  payload: Array<{ id?: string; name: string; capacity: number; resource_type: string; user_ref_id?: string | null }>,
) {
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

export async function appointmentActivity(appointmentTypeId: string): Promise<ActivityItem[]> {
  const res = await api.get<ActivityItem[]>(`/appointment-types/${appointmentTypeId}/activity`)
  return res.data
}

export async function addAppointmentNote(appointmentTypeId: string, message: string): Promise<ActivityItem> {
  const res = await api.post<ActivityItem>(`/appointment-types/${appointmentTypeId}/notes`, { message })
  return res.data
}

export async function sendAppointmentMessage(appointmentTypeId: string, message: string): Promise<ActivityItem> {
  const res = await api.post<ActivityItem>(`/appointment-types/${appointmentTypeId}/messages`, { message })
  return res.data
}
