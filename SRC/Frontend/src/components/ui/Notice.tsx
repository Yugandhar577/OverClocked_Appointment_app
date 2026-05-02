import { clsx } from "clsx"

export function Notice({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "error" | "success" }) {
  return (
    <div
      className={clsx(
        "rounded-md border px-4 py-3 text-sm",
        tone === "neutral" && "border-line bg-white text-ink",
        tone === "error" && "border-red-200 bg-red-50 text-red-700",
        tone === "success" && "border-green-200 bg-green-50 text-moss",
      )}
    >
      {children}
    </div>
  )
}
