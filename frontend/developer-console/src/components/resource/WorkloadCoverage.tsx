import type { WorkloadCounts } from "@/types/api";

/** Explicit measurement coverage — never rounded up to imply completeness. */
export function WorkloadCoverage({ counts }: { counts: WorkloadCounts }) {
  const segments = [
    { value: counts.measured, className: "bg-success", label: "Measured" },
    { value: counts.partial, className: "bg-warning", label: "Partial" },
    { value: counts.insufficient_data, className: "bg-muted-foreground/35", label: "Insufficient data" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-5">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Total</p>
        <p className="mt-1 text-lg font-semibold tabular-nums">{counts.total.toLocaleString()}</p>
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Measured
        </p>
        <p className="mt-1 text-lg font-semibold tabular-nums">
          {counts.measured.toLocaleString()}
        </p>
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Partial
        </p>
        <p className="mt-1 text-lg font-semibold tabular-nums">
          {counts.partial.toLocaleString()}
        </p>
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Insufficient data
        </p>
        <p className="mt-1 text-lg font-semibold tabular-nums">
          {counts.insufficient_data.toLocaleString()}
        </p>
      </div>
      <div className="col-span-2 border-l-0 lg:col-span-1 lg:border-l lg:border-border lg:pl-4">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Coverage</p>
        <p className="mt-1 text-2xl font-semibold tabular-nums">{counts.coverage_percent}%</p>
      </div>
      </div>
      <div>
        <div className="flex h-2 overflow-hidden rounded-sm bg-muted" aria-hidden="true">
          {counts.total > 0
            ? segments.map((segment) => (
                <span
                  key={segment.label}
                  className={segment.className}
                  style={{ width: `${(segment.value / counts.total) * 100}%` }}
                />
              ))
            : null}
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Coverage represents the share of workloads for which defensible methodology data is available.
        </p>
      </div>
    </div>
  );
}
