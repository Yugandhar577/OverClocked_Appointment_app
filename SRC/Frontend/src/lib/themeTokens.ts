import type { ThemeSettings } from "../api/advanced"

export const DEFAULT_THEME = {
  primaryColor: "#714B67",
  secondaryColor: "#017E84",
  accentColor: "#00A09D",
  backgroundColor: "#F8F9FA",
  cardColor: "#FFFFFF",
  borderColor: "#D8DADD",
  successColor: "#28A745",
  warningColor: "#F0AD4E",
  errorColor: "#DC3545",
  sidebarColor: "#F3F4F6",
  headerColor: "#FFFFFF",
  buttonStyle: "solid",
  roundedness: "8px",
  mode: "light",
}

const CSS_TOKEN_MAP: Record<string, string> = {
  primaryColor: "--odoo-primary",
  secondaryColor: "--odoo-secondary",
  accentColor: "--odoo-accent",
  backgroundColor: "--odoo-bg",
  cardColor: "--odoo-card",
  borderColor: "--odoo-border",
  successColor: "--odoo-success",
  warningColor: "--odoo-warning",
  errorColor: "--odoo-error",
  sidebarColor: "--odoo-sidebar",
  headerColor: "--odoo-header",
  roundedness: "--odoo-radius",
}

export function applyTheme(theme?: ThemeSettings | null) {
  const values = { ...DEFAULT_THEME, ...(theme?.settings ?? {}) }
  for (const [key, cssVar] of Object.entries(CSS_TOKEN_MAP)) {
    document.documentElement.style.setProperty(cssVar, values[key as keyof typeof DEFAULT_THEME])
  }
  document.documentElement.dataset.themeMode = values.mode
}
