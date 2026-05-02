import { RotateCcw, Save } from "lucide-react"
import { useEffect, useState } from "react"

import { resetTheme } from "../../api/advanced"
import { errorMessage } from "../../api/client"
import { useThemeSettings } from "../../auth/ThemeProvider"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { DEFAULT_THEME } from "../../lib/themeTokens"

const COLOR_FIELDS = [
  ["primaryColor", "Primary"],
  ["secondaryColor", "Secondary"],
  ["accentColor", "Accent"],
  ["backgroundColor", "Background"],
  ["cardColor", "Card"],
  ["borderColor", "Border"],
  ["successColor", "Success"],
  ["warningColor", "Warning"],
  ["errorColor", "Error"],
  ["sidebarColor", "Sidebar"],
  ["headerColor", "Header"],
] as const

export function ThemeSettingsPage() {
  const { theme, reloadTheme, previewTheme, persistTheme } = useThemeSettings()
  const [settings, setSettings] = useState<Record<string, string>>(DEFAULT_THEME)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    setSettings({ ...DEFAULT_THEME, ...(theme?.settings ?? {}) })
  }, [theme])

  function update(key: string, value: string) {
    const next = { ...settings, [key]: value }
    setSettings(next)
    previewTheme(next)
  }

  async function save() {
    setError("")
    try {
      await persistTheme({ name: "Odoo Default", settings })
      setMessage("Theme saved.")
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function reset() {
    setError("")
    try {
      await resetTheme()
      await reloadTheme()
      setMessage("Theme reset to Odoo default.")
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Theme Customization</h1>
        <p className="text-sm text-neutral-600">Adjust Odoo-style colors, roundedness, and light or dark mode.</p>
      </div>
      {message && <Notice tone="success">{message}</Notice>}
      {error && <Notice tone="error">{error}</Notice>}
      <div className="odoo-surface grid gap-4 p-4 md:grid-cols-2">
        {COLOR_FIELDS.map(([key, label]) => (
          <label key={key} className="flex items-center justify-between gap-4 text-sm font-semibold">
            {label}
            <input className="h-10 w-20 rounded border border-line" type="color" value={settings[key] ?? "#000000"} onChange={(event) => update(key, event.target.value)} />
          </label>
        ))}
        <label className="flex items-center justify-between gap-4 text-sm font-semibold">
          Roundedness
          <select className="h-10 rounded border border-line bg-white px-3" value={settings.roundedness} onChange={(event) => update("roundedness", event.target.value)}>
            <option value="4px">Compact</option>
            <option value="8px">Odoo default</option>
            <option value="12px">Soft</option>
          </select>
        </label>
        <label className="flex items-center justify-between gap-4 text-sm font-semibold">
          Mode
          <select className="h-10 rounded border border-line bg-white px-3" value={settings.mode} onChange={(event) => update("mode", event.target.value)}>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </div>
      <div className="flex gap-2">
        <Button onClick={save}><Save size={16} /> Save</Button>
        <Button variant="secondary" onClick={reset}><RotateCcw size={16} /> Reset</Button>
      </div>
    </section>
  )
}
