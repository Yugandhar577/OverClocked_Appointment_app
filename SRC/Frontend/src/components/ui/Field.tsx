import { clsx } from "clsx"
import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react"

export function Label({ children }: { children: React.ReactNode }) {
  return <label className="text-sm font-semibold text-ink">{children}</label>
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(props, ref) {
  return (
    <input
      {...props}
      ref={ref}
      className={clsx(
        "focus-ring h-10 rounded-md border bg-white px-3 text-sm text-ink transition-colors",
        props["aria-invalid"] ? "border-red-400 focus:ring-red-200" : "border-line",
        props.className,
      )}
    />
  )
})

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={clsx(
        "focus-ring h-10 rounded-md border bg-white px-3 text-sm text-ink transition-colors",
        props["aria-invalid"] ? "border-red-400" : "border-line",
        props.className,
      )}
    />
  )
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={clsx(
        "focus-ring min-h-24 rounded-md border bg-white px-3 py-2 text-sm text-ink transition-colors",
        props["aria-invalid"] ? "border-red-400" : "border-line",
        props.className,
      )}
    />
  )
}

export function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}
