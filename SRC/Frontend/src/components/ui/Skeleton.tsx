import { clsx } from "clsx"

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden="true" className={clsx("animate-pulse rounded-md bg-line/70", className)} />
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="grid gap-2">
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton key={index} className={index === lines - 1 ? "h-3 w-2/3" : "h-3 w-full"} />
      ))}
    </div>
  )
}
