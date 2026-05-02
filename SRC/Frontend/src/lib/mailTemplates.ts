export type MailTemplateType = "booking" | "cancellation" | "email_reminder" | "sms_reminder"

export interface MailTemplate {
  id: string
  name: string
  type: MailTemplateType
  source: "System" | "Custom"
  subject: string
  body: string
  updated_at: string
}

const STORAGE_KEY = "overclocked.mailTemplates.v1"

export const templateTokens = [
  "{{customer_name}}",
  "{{customer_email}}",
  "{{customer_phone}}",
  "{{appointment_type}}",
  "{{appointment_date}}",
  "{{appointment_time}}",
  "{{confirmation_code}}",
  "{{organization_name}}",
  "{{venue}}",
]

const defaults: MailTemplate[] = [
  {
    id: "booking-confirmation",
    name: "Booking Confirmation",
    type: "booking",
    source: "System",
    subject: "Booking confirmed: {{appointment_type}}",
    body:
      "Hi {{customer_name}},\n\nYour booking is confirmed!\n\nService: {{appointment_type}}\nDate: {{appointment_date}}\nTime: {{appointment_time}}\nVenue: {{venue}}\nConfirmation code: {{confirmation_code}}\n\nThank you,\n{{organization_name}}",
    updated_at: "2026-05-03T01:48:29.000Z",
  },
  {
    id: "cancellation",
    name: "Cancellation",
    type: "cancellation",
    source: "System",
    subject: "Booking cancelled: {{appointment_type}}",
    body:
      "Hi {{customer_name}},\n\nYour booking for {{appointment_type}} on {{appointment_date}} at {{appointment_time}} was cancelled.\n\nThank you,\n{{organization_name}}",
    updated_at: "2026-05-03T01:48:29.000Z",
  },
  {
    id: "reminder-email",
    name: "Reminder Email",
    type: "email_reminder",
    source: "System",
    subject: "Reminder: {{appointment_type}} at {{appointment_time}}",
    body:
      "Hi {{customer_name}},\n\nThis is a reminder for {{appointment_type}} on {{appointment_date}} at {{appointment_time}}.\n\nVenue: {{venue}}\nConfirmation code: {{confirmation_code}}",
    updated_at: "2026-05-03T01:48:29.000Z",
  },
  {
    id: "reminder-sms",
    name: "Reminder SMS",
    type: "sms_reminder",
    source: "System",
    subject: "Reminder SMS",
    body: "{{appointment_type}} reminder: {{appointment_date}} at {{appointment_time}}. Code {{confirmation_code}}.",
    updated_at: "2026-05-03T01:48:29.000Z",
  },
]

export function templateTypeLabel(type: MailTemplateType) {
  const labels: Record<MailTemplateType, string> = {
    booking: "Booking",
    cancellation: "Cancellation",
    email_reminder: "Email reminder",
    sms_reminder: "SMS reminder",
  }
  return labels[type]
}

export function listMailTemplates(): MailTemplate[] {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (!stored) return defaults
  try {
    const custom = JSON.parse(stored) as MailTemplate[]
    const customById = new Map(custom.map((item) => [item.id, item]))
    return defaults.map((item) => customById.get(item.id) ?? item).concat(custom.filter((item) => !defaults.some((base) => base.id === item.id)))
  } catch {
    return defaults
  }
}

export function getMailTemplate(id: string) {
  return listMailTemplates().find((item) => item.id === id)
}

export function saveMailTemplate(template: MailTemplate) {
  const next = listMailTemplates().map((item) => (item.id === template.id ? template : item))
  if (!next.some((item) => item.id === template.id)) next.unshift(template)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next.filter((item) => item.source === "Custom")))
  return template
}

export function createMailTemplate(input: Omit<MailTemplate, "id" | "source" | "updated_at">) {
  return saveMailTemplate({
    ...input,
    id: crypto.randomUUID(),
    source: "Custom",
    updated_at: new Date().toISOString(),
  })
}

export function renderTemplate(value: string) {
  const replacements: Record<string, string> = {
    "{{customer_name}}": "John Doe",
    "{{customer_email}}": "john@example.com",
    "{{customer_phone}}": "+91 98765 43210",
    "{{appointment_type}}": "30-min Consultation",
    "{{appointment_date}}": "May 7, 2026",
    "{{appointment_time}}": "11:00 AM",
    "{{confirmation_code}}": "DEMO123",
    "{{organization_name}}": "OverClocked",
    "{{venue}}": "Room 201, VIT Pune",
  }
  return Object.entries(replacements).reduce((text, [token, replacement]) => text.replaceAll(token, replacement), value)
}
