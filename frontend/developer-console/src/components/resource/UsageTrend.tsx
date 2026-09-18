import { useState } from "react";

import { MetricStatusBadge } from "@/components/resource/MetricRangeDisplay";
import { Button } from "@/components/ui/button";
import { formatDateTime, formatRange } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";
import type { AggregateMetricRange, UsageTimeseriesPoint } from "@/types/api";

type ResourceKey = "energy" | "water" | "carbon";

const RESOURCES: Array<{ key: ResourceKey; label: string }> = [
  { key: "energy", label: "Energy" },
  { key: "water", label: "Water" },
  { key: "carbon", label: "Carbon" },
];

/**
 * An uncertainty-band view: the upper and lower edges are the API's max and
 * min values. No midpoint is calculated or drawn. Missing buckets break the
 * band rather than being plotted as zero.
 */
export function UsageTrend({ points }: { points: UsageTimeseriesPoint[] }) {
  const [resource, setResource] = useState<ResourceKey>("energy");
  const available = points.filter((point) => hasRange(point[resource]));
  const values = available.flatMap((point) => [point[resource].min, point[resource].max]);
  const numericValues = values.filter((value): value is number => value != null);
  const minimum = numericValues.length > 0 ? Math.min(...numericValues) : 0;
  const maximum = numericValues.length > 0 ? Math.max(...numericValues) : 0;
  const span = maximum - minimum || 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1" role="group" aria-label="Trend resource">
        {RESOURCES.map((item) => (
          <Button
            key={item.key}
            size="sm"
            variant={resource === item.key ? "secondary" : "ghost"}
            aria-pressed={resource === item.key}
            onClick={() => setResource(item.key)}
          >
            {item.label}
          </Button>
        ))}
      </div>

      <div className="rounded-[var(--radius-console)] border border-border bg-background/40 p-4">
        <div
          className="grid h-48 items-end gap-1.5 sm:gap-2"
          style={{ gridTemplateColumns: `repeat(${points.length}, minmax(10px, 1fr))` }}
          role="img"
          aria-label={`${RESOURCES.find((item) => item.key === resource)?.label} minimum-to-maximum ranges over time`}
        >
          {points.map((point) => {
            const metric = point[resource];
            const valid = hasRange(metric);
            const lower = valid ? (((metric.min ?? minimum) - minimum) / span) * 82 : 0;
            const upper = valid ? (((metric.max ?? minimum) - minimum) / span) * 82 : 0;
            const height = valid ? Math.max(5, upper - lower) : 0;
            return (
              <div
                key={point.period_start}
                className="group relative flex h-full items-end justify-center"
                title={trendTitle(point, metric)}
              >
                {valid ? (
                  <div
                    className={cn(
                      "absolute w-full max-w-10 rounded-sm border border-primary/60 bg-primary/20 transition-colors group-hover:bg-primary/35",
                      metric.status === "partial" && "border-dashed border-warning/70 bg-warning/15",
                    )}
                    style={{ bottom: `${lower}%`, height: `${height}%` }}
                  />
                ) : (
                  <div className="mb-1 h-1 w-full max-w-8 border-t border-dashed border-muted-foreground/50" />
                )}
              </div>
            );
          })}
        </div>
        <div className="mt-2 grid grid-cols-[1fr_auto_1fr] text-[11px] text-muted-foreground">
          <span>{formatDateTime(points[0]?.period_start ?? "")}</span>
          <span className="text-center">Range band · no midpoint</span>
          <span className="text-right">{formatDateTime(points.at(-1)?.period_start ?? "")}</span>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3" aria-label="Trend values">
        {points.map((point) => {
          const metric = point[resource];
          return (
            <div key={point.period_start} className="rounded border border-border px-3 py-2 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-muted-foreground">{formatDateTime(point.period_start)}</span>
                <MetricStatusBadge status={metric.status} />
              </div>
              <p className="mt-1 font-mono tabular-nums text-foreground">
                {hasRange(metric)
                  ? `${formatRange(metric.min ?? 0, metric.max ?? 0)} ${metric.unit}`
                  : "Insufficient data"}
              </p>
              <p className="mt-0.5 text-muted-foreground">
                {point.workloads.total.toLocaleString()} workloads · {point.workloads.coverage_percent}% coverage
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function hasRange(metric: AggregateMetricRange) {
  return metric.status !== "insufficient_data" && metric.min != null && metric.max != null;
}

function trendTitle(point: UsageTimeseriesPoint, metric: AggregateMetricRange) {
  const value = hasRange(metric)
    ? `${formatRange(metric.min ?? 0, metric.max ?? 0)} ${metric.unit}`
    : "Insufficient data";
  return `${formatDateTime(point.period_start)}: ${value}; ${point.workloads.coverage_percent}% coverage`;
}
