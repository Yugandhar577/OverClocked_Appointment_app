import { clsx } from "clsx"

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "inline-flex rounded-full border px-2 py-1 text-xs font-semibold capitalize",
        status === "confirmed" && "border-moss bg-green-50 text-moss",
        status === "pending" && "border-amber-300 bg-amber-50 text-amber-800",
        status === "cancelled" && "border-red-200 bg-red-50 text-red-700",
        status === "rescheduled" && "border-blue-200 bg-blue-50 text-blue-700",
        status === "completed" && "border-line bg-white text-ink",
      )}
    >
      {status}
    </span>
  )
}
