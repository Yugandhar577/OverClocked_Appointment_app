import { api } from "./client"
import type { User } from "./types"

export interface LoginResponse {
  access_token: string
  token_type: "bearer"
  user: User
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await api.post<LoginResponse>("/auth/login", { email, password })
  return res.data
}

export async function signup(full_name: string, email: string, password: string) {
  const res = await api.post("/auth/signup", { full_name, email, password, timezone: "Asia/Kolkata" })
  return res.data as { user_id: string; message: string }
}

export async function verifyOtp(email: string, otp: string) {
  const res = await api.post("/auth/verify-otp", { email, otp })
  return res.data as { verified: boolean }
}

export async function me(): Promise<User> {
  const res = await api.get<User>("/auth/me")
  return res.data
}

export async function updateMe(payload: Partial<Pick<User, "full_name" | "phone" | "timezone">>): Promise<User> {
  const res = await api.patch<User>("/auth/me", payload)
  return res.data
}
