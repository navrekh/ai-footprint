import type { WorkloadCounts } from "@/types/api";

/** Explicit measurement coverage — never rounded up to imply completeness. */
export function WorkloadCoverage({ counts }: { counts: WorkloadCounts }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
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
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Coverage
        </p>
        <p className="mt-1 text-lg font-semibold tabular-nums">{counts.coverage_percent}%</p>
      </div>
    </div>
  );
}
