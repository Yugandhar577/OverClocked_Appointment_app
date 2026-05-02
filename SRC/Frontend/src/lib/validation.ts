import { z } from "zod"

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Enter a valid email address (e.g. you@example.com)"),
  password: z.string().min(1, "Password is required"),
})

export const signupSchema = z.object({
  fullName: z
    .string()
    .min(1, "Full name is required")
    .min(2, "Full name must be at least 2 characters")
    .max(150, "Full name must be at most 150 characters"),
  email: z
    .string()
    .min(1, "Email is required")
    .email("Enter a valid email address (e.g. you@example.com)"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter (A–Z)")
    .regex(/[0-9]/, "Password must contain at least one number (0–9)"),
})

export const otpSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Enter a valid email address"),
  otp: z
    .string()
    .min(1, "OTP is required")
    .min(4, "OTP must be at least 4 digits")
    .max(8, "OTP must be at most 8 digits")
    .regex(/^\d+$/, "OTP must contain only digits (0–9)"),
})

export const profileSchema = z.object({
  fullName: z
    .string()
    .min(1, "Full name is required")
    .min(2, "Full name must be at least 2 characters")
    .max(150, "Full name must be at most 150 characters"),
  phone: z
    .string()
    .max(20, "Phone must be at most 20 characters")
    .regex(/^[\d\s+\-()\[\]]*$/, "Enter a valid phone number (digits, spaces, +, -, ( ) only)")
    .or(z.literal(""))
    .optional(),
})

export const notificationSettingsSchema = z.object({
  reminder_email_hours: z.coerce.number().int().min(0, "Must be 0 or more").max(720, "Max 720 hours").nullable(),
  reminder_sms_hours: z.coerce.number().int().min(0, "Must be 0 or more").max(720, "Max 720 hours").nullable(),
  email_enabled: z.boolean(),
  sms_enabled: z.boolean(),
  sender_name: z.string().min(1, "Sender name is required").max(120, "Max 120 characters"),
  reminder_email_subject: z.string().min(1, "Subject is required").max(200, "Max 200 characters"),
  reminder_email_body: z.string().min(1, "Body is required").max(5000, "Max 5000 characters"),
  reminder_sms_body: z.string().max(480, "Max 480 characters"),
  booking_confirmation_subject: z.string().min(1, "Subject is required").max(200, "Max 200 characters"),
  booking_confirmation_body: z.string().min(1, "Body is required").max(5000, "Max 5000 characters"),
  cancellation_subject: z.string().min(1, "Subject is required").max(200, "Max 200 characters"),
  cancellation_body: z.string().min(1, "Body is required").max(5000, "Max 5000 characters"),
})

export type LoginFormData = z.infer<typeof loginSchema>
export type SignupFormData = z.infer<typeof signupSchema>
export type OtpFormData = z.infer<typeof otpSchema>
export type ProfileFormData = z.infer<typeof profileSchema>
export type NotificationSettingsFormData = z.infer<typeof notificationSettingsSchema>
