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

export const mailTemplateSchema = z.object({
  template_type: z.enum(["booking_confirmation", "cancellation", "reminder_email", "reminder_sms"]),
  name: z.string().min(1, "Name is required").max(200, "Max 200 characters"),
  subject: z.string().max(300, "Max 300 characters").nullable().optional(),
  body_html: z.string().min(1, "Body is required").max(50000, "Max 50000 characters"),
  description: z.string().max(1000, "Max 1000 characters").nullable().optional(),
})

export const reminderSchema = z.object({
  channel: z.enum(["email", "sms"]),
  hours_before: z.coerce.number().int().min(0, "Must be 0 or more").max(720, "Max 720 hours"),
})

export type LoginFormData = z.infer<typeof loginSchema>
export type SignupFormData = z.infer<typeof signupSchema>
export type OtpFormData = z.infer<typeof otpSchema>
export type ProfileFormData = z.infer<typeof profileSchema>
export type MailTemplateFormData = z.infer<typeof mailTemplateSchema>
export type ReminderFormData = z.infer<typeof reminderSchema>
