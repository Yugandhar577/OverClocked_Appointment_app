import type { ReactNode } from "react"
import { createContext, useCallback, useContext, useEffect, useState } from "react"

import { getTheme, saveTheme, type ThemeSettings } from "../api/advanced"
import { applyTheme } from "../lib/themeTokens"

interface ThemeContextValue {
  theme: ThemeSettings | null
  reloadTheme: () => Promise<void>
  previewTheme: (settings: Record<string, string>) => void
  persistTheme: (payload: { name: string; settings: Record<string, string> }) => Promise<ThemeSettings>
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<ThemeSettings | null>(null)

  const reloadTheme = useCallback(async () => {
    const next = await getTheme()
    setTheme(next)
    applyTheme(next)
  }, [])

  const previewTheme = useCallback((settings: Record<string, string>) => {
    applyTheme({ id: null, name: "Preview", settings, is_default: false })
  }, [])

  const persistTheme = useCallback(async (payload: { name: string; settings: Record<string, string> }) => {
    const next = await saveTheme(payload)
    setTheme(next)
    applyTheme(next)
    return next
  }, [])

  useEffect(() => {
    reloadTheme().catch(() => applyTheme(null))
  }, [reloadTheme])

  return <ThemeContext.Provider value={{ theme, reloadTheme, previewTheme, persistTheme }}>{children}</ThemeContext.Provider>
}

export function useThemeSettings() {
  const value = useContext(ThemeContext)
  if (!value) throw new Error("useThemeSettings must be used inside ThemeProvider")
  return value
}
