import { createContext, useCallback, useEffect, useMemo, useState } from "react"

import * as authApi from "../api/auth"
import type { User } from "../api/types"

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => void
  refresh: () => Promise<void>
  hasRole: (...roles: string[]) => boolean
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("access_token"))
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem("access_token")
    setToken(null)
    setUser(null)
  }, [])

  const refresh = useCallback(async () => {
    const stored = localStorage.getItem("access_token")
    if (!stored) {
      setLoading(false)
      return
    }
    try {
      setToken(stored)
      setUser(await authApi.me())
    } catch {
      logout()
    } finally {
      setLoading(false)
    }
  }, [logout])

  useEffect(() => {
    refresh()
    window.addEventListener("auth:logout", logout)
    return () => window.removeEventListener("auth:logout", logout)
  }, [logout, refresh])

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password)
    localStorage.setItem("access_token", res.access_token)
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      login,
      logout,
      refresh,
      hasRole: (...roles: string[]) => Boolean(user?.roles.some((role) => roles.includes(role))),
    }),
    [loading, login, logout, refresh, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
