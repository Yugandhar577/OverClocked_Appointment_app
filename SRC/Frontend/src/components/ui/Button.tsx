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
        variant === "primary" && "border-ink bg-ink text-paper hover:bg-moss",
        variant === "secondary" && "border-line bg-white text-ink hover:border-ink",
        variant === "ghost" && "border-transparent bg-transparent text-ink hover:bg-white",
        variant === "danger" && "border-warn bg-warn text-white hover:bg-red-800",
        className,
      )}
      {...props}
    />
  )
}
