import { api } from "./client"

export interface NotificationSettings {
  id: string
  organization_id: string | null
  reminder_email_hours: number | null
  reminder_sms_hours: number | null
  email_enabled: boolean
  sms_enabled: boolean
  sender_name: string
  reminder_email_subject: string
  reminder_email_body: string
  reminder_sms_body: string
  booking_confirmation_subject: string
  booking_confirmation_body: string
  cancellation_subject: string
  cancellation_body: string
  updated_at: string
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
  const res = await api.get<NotificationSettings>("/organiser/notification-settings")
  return res.data
}

export async function updateNotificationSettings(
  payload: Partial<Omit<NotificationSettings, "id" | "organization_id" | "updated_at">>,
): Promise<NotificationSettings> {
  const res = await api.put<NotificationSettings>("/organiser/notification-settings", payload)
  return res.data
}

export async function getNotificationPlaceholders(): Promise<string[]> {
  const res = await api.get<{ placeholders: string[] }>("/organiser/notification-settings/placeholders")
  return res.data.placeholders
}
