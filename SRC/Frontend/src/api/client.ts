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

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === "string") return detail.replaceAll("_", " ")
    if (detail?.detail) return String(detail.detail).replaceAll("_", " ")
    return error.message
  }
  return "Something went wrong"
}
