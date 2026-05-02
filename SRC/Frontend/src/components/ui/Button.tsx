import { clsx } from "clsx"
import type { ButtonHTMLAttributes } from "react"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger"
}

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-md border px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "border-primary bg-primary text-white hover:bg-[var(--odoo-secondary)]",
        variant === "secondary" && "border-[var(--odoo-border)] bg-[var(--odoo-card)] text-ink hover:border-primary",
        variant === "ghost" && "border-transparent bg-transparent text-ink hover:bg-white",
        variant === "danger" && "border-[var(--odoo-error)] bg-[var(--odoo-error)] text-white hover:bg-red-800",
        className,
      )}
      {...props}
    />
  )
}
