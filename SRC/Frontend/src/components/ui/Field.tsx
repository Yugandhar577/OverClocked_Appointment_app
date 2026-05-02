import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react"
import { clsx } from "clsx"

export function Label({ children }: { children: React.ReactNode }) {
  return <label className="text-sm font-semibold text-ink">{children}</label>
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={clsx("focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm text-ink", props.className)} />
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={clsx("focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm text-ink", props.className)} />
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={clsx("focus-ring min-h-24 rounded-md border border-line bg-white px-3 py-2 text-sm text-ink", props.className)} />
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
    </div>
  )
}
