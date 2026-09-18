import { cn } from "@/lib/utils/cn";

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded bg-muted", className)} />;
}

export function TableSkeleton({ rows = 4, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="rounded-[var(--radius-console)] border border-border bg-surface"
    >
      <span className="sr-only">Loading</span>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex items-center gap-4 border-b border-border px-4 py-4 last:border-b-0"
        >
          {Array.from({ length: columns }).map((__, colIndex) => (
            <Skeleton key={colIndex} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
    >
      <span className="sr-only">Loading</span>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="rounded-[var(--radius-console)] border border-border bg-surface p-5"
        >
          <Skeleton className="h-3 w-24" />
          <Skeleton className="mt-4 h-7 w-16" />
        </div>
      ))}
    </div>
  );
}
