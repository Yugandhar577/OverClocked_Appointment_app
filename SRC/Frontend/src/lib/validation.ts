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

export type LoginFormData = z.infer<typeof loginSchema>
export type SignupFormData = z.infer<typeof signupSchema>
export type OtpFormData = z.infer<typeof otpSchema>
export type ProfileFormData = z.infer<typeof profileSchema>
