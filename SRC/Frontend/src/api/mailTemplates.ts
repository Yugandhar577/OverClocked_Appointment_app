import { api } from "./client"

export type TemplateType = "booking_confirmation" | "cancellation" | "reminder_email" | "reminder_sms"

export interface MailTemplate {
  id: string
  organization_id: string | null
  template_type: TemplateType
  name: string
  subject: string | null
  body_html: string
  description: string | null
  is_system_default: boolean
  can_edit: boolean
  updated_at: string
}

export interface MailTemplatePayload {
  template_type: TemplateType
  name: string
  subject?: string | null
  body_html: string
  description?: string | null
}

export async function listMailTemplates(): Promise<MailTemplate[]> {
  const res = await api.get<MailTemplate[]>("/organiser/mail-templates")
  return res.data
}

export async function getMailTemplate(id: string): Promise<MailTemplate> {
  const res = await api.get<MailTemplate>(`/organiser/mail-templates/${id}`)
  return res.data
}

export async function createMailTemplate(payload: MailTemplatePayload): Promise<MailTemplate> {
  const res = await api.post<MailTemplate>("/organiser/mail-templates", payload)
  return res.data
}

export async function updateMailTemplate(id: string, payload: Partial<Omit<MailTemplatePayload, "template_type">>): Promise<MailTemplate> {
  const res = await api.put<MailTemplate>(`/organiser/mail-templates/${id}`, payload)
  return res.data
}

export async function resetMailTemplate(id: string): Promise<MailTemplate> {
  const res = await api.post<MailTemplate>(`/organiser/mail-templates/${id}/reset`)
  return res.data
}

export async function previewMailTemplate(id: string, sampleAppointmentId?: string): Promise<{ subject: string | null; body_html: string }> {
  const res = await api.post<{ subject: string | null; body_html: string }>(`/organiser/mail-templates/${id}/preview`, {
    sample_appointment_id: sampleAppointmentId,
  })
  return res.data
}

export async function getTemplatePlaceholders(): Promise<string[]> {
  const res = await api.get<{ placeholders: string[] }>("/organiser/mail-templates/placeholders")
  return res.data.placeholders
}
