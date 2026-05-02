export function formatDateTime(value?: string | null) {
  if (!value) return "-"
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

export function formatTime(value?: string | null) {
  if (!value) return "-"
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value))
}

export function todayIsoDate() {
  return new Date().toISOString().slice(0, 10)
}
