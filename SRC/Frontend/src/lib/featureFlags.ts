import { getFeatureFlags, type FeatureFlags } from "../api/advanced"

export const DEFAULT_FEATURE_FLAGS: FeatureFlags = {
  ENABLE_WAITLIST: false,
  ENABLE_BOOKING_CART: false,
  ENABLE_VARIABLE_DURATION: false,
  ENABLE_RECURRING_BOOKINGS: false,
  ENABLE_NO_SHOW_PROTECTION: false,
  ENABLE_SMART_ASSIGNMENT: false,
  ENABLE_DYNAMIC_PRICING: false,
  ENABLE_NOTIFICATION_WORKFLOWS: false,
  ENABLE_ADMIN_MANUAL_BOOKING: false,
  ENABLE_APPOINTMENT_ANALYTICS: false,
  ENABLE_THEME_CUSTOMIZATION: false,
  ENABLE_ODOO_STYLE_UI: false,
}

let cachedFlags = DEFAULT_FEATURE_FLAGS

export async function loadFeatureFlags() {
  try {
    cachedFlags = { ...DEFAULT_FEATURE_FLAGS, ...(await getFeatureFlags()) }
  } catch {
    cachedFlags = DEFAULT_FEATURE_FLAGS
  }
  return cachedFlags
}

export function isFeatureEnabled(flag: keyof typeof DEFAULT_FEATURE_FLAGS) {
  return Boolean(cachedFlags[flag])
}
