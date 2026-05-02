import axios from "axios"

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 15_000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = String(error.config?.url ?? "")
    if (error.response?.status === 401 && !url.endsWith("/auth/login")) {
      localStorage.removeItem("access_token")
      window.dispatchEvent(new Event("auth:logout"))
    }
    return Promise.reject(error)
  },
)

const API_MESSAGES: Record<string, string> = {
  invalid_credentials: "Email or password is incorrect.",
  account_unverified:
    "This email is not verified yet. Finish signup with the code we sent you (see the OTP page), then try logging in.",
  account_disabled: "This account has been disabled.",
  otp_expired: "That verification or reset link has expired. Request a new one.",
  email_exists: "An account with this email already exists.",
}

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === "string") {
      return API_MESSAGES[detail] ?? detail.replaceAll("_", " ")
    }
    if (detail?.detail && typeof detail.detail === "string") {
      const code = detail.detail as string
      return API_MESSAGES[code] ?? String(code).replaceAll("_", " ")
    }
    const status = error.response?.status
    if (!error.response) {
      return "Cannot reach the API. Is the backend running (e.g. http://localhost:8000)?"
    }
    if (status === 401) return API_MESSAGES.invalid_credentials
    return error.message
  }
  return "Something went wrong"
}
