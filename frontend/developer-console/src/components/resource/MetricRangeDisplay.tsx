import { Badge } from "@/components/ui/badge";
import { formatRange } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";
import type { AggregateMetricRange, MetricRange, NormalizedMetricRange } from "@/types/api";

/**
 * The single place this console renders a resource-impact range. This is
 * the core product-invariant boundary: it must never collapse min/max into
 * an average, never show "0" or "N/A" for insufficient data, and must
 * always reflect the status the backend actually reported.
 */
export function MetricStatusBadge({ status }: { status: string }) {
  const tone = status === "ok" ? "active" : status === "partial" ? "warning" : "neutral";
  const label =
    status === "ok" ? "Measured" : status === "partial" ? "Partial" : "Insufficient data";
  return <Badge tone={tone}>{label}</Badge>;
}

export function MetricRangeDisplay({
  label,
  range,
  showStatus = true,
  compact = false,
}: {
  label?: string;
  range: MetricRange | AggregateMetricRange | NormalizedMetricRange;
  showStatus?: boolean;
  /** Smaller type, for use inside table cells rather than a standalone card. */
  compact?: boolean;
}) {
  const hasRange = range.status !== "insufficient_data" && range.min != null && range.max != null;
  const coverage =
    "total_workloads" in range
      ? `${range.measured_workloads.toLocaleString()} of ${range.total_workloads.toLocaleString()} workloads measured`
      : null;

  return (
    <div>
      {label ? (
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
      ) : null}
      {hasRange ? (
        <p
          className={cn(
            "font-semibold tabular-nums text-foreground",
            compact ? "text-sm" : "mt-1 text-lg",
          )}
        >
          {formatRange(range.min as number, range.max as number)}{" "}
          <span className="text-xs font-normal text-muted-foreground">{range.unit}</span>
        </p>
      ) : (
        <p
          className={cn(
            "font-semibold text-muted-foreground",
            compact ? "text-sm" : "mt-1 text-lg",
          )}
        >
          Insufficient data
        </p>
      )}
      {showStatus || coverage ? (
        <div className="mt-1 flex flex-wrap items-center gap-2">
          {showStatus ? <MetricStatusBadge status={range.status} /> : null}
          {coverage ? <span className="text-xs text-muted-foreground">{coverage}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

export function ResourceRangesGrid({
  energy,
  water,
  carbon,
}: {
  energy: MetricRange | AggregateMetricRange | NormalizedMetricRange;
  water: MetricRange | AggregateMetricRange | NormalizedMetricRange;
  carbon: MetricRange | AggregateMetricRange | NormalizedMetricRange;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <MetricRangeDisplay label="Energy" range={energy} />
      <MetricRangeDisplay label="Water" range={water} />
      <MetricRangeDisplay label="Carbon" range={carbon} />
    </div>
  );
}
