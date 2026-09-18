import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { EstimateDetails } from "@/components/resource/EstimateDetails";
import { MetricStatusBadge, ResourceRangesGrid } from "@/components/resource/MetricRangeDisplay";
import { formatMetricValue, formatRange } from "@/lib/utils/format";
import type { ComparisonResultItem } from "@/types/api";

/**
 * One candidate's independent outcome (shared by Compare and Benchmarks).
 * Rendered in the exact order the API returned it — this component never
 * sorts, scores, or marks a candidate as a "winner." Each candidate stands
 * alone; the developer draws their own conclusions.
 */
export function ComparisonResultCard({
  result,
  index,
}: {
  result: ComparisonResultItem;
  index: number;
}) {
  const identity = result.resolved ?? result.candidate;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Candidate {index + 1}
          </p>
          <p className="mt-0.5 text-sm font-semibold text-foreground">
            {identity.provider} / {identity.model}
            {identity.model_version ? (
              <span className="font-mono text-xs font-normal text-muted-foreground">
                {" "}
                @ {identity.model_version}
              </span>
            ) : null}
          </p>
          {result.resolved &&
          (result.resolved.model_version ?? null) !== (result.candidate.model_version ?? null) ? (
            <p className="mt-0.5 text-xs text-muted-foreground">
              Requested as {result.candidate.provider}/{result.candidate.model}
              {result.candidate.model_version ? ` @ ${result.candidate.model_version}` : ""}
            </p>
          ) : null}
        </div>
        <Badge tone={result.status === "success" ? "active" : "danger"}>
          {result.status === "success" ? "Success" : "Failed"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        {result.status === "success" && result.estimate ? (
          <>
            <ResourceRangesGrid
              energy={result.estimate.energy}
              water={result.estimate.water}
              carbon={result.estimate.carbon}
            />
            {result.normalized ? (
              <div className="rounded-[var(--radius-console)] border border-border bg-surface-raised/50 p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Normalized — per {formatMetricValue(result.normalized.denominator.value)}{" "}
                  {result.normalized.denominator.unit}
                </p>
                <div className="mt-2 grid gap-3 sm:grid-cols-3">
                  {result.normalized.energy ? (
                    <NormalizedMetric label="Energy" metric={result.normalized.energy} />
                  ) : null}
                  {result.normalized.water ? (
                    <NormalizedMetric label="Water" metric={result.normalized.water} />
                  ) : null}
                  {result.normalized.carbon ? (
                    <NormalizedMetric label="Carbon" metric={result.normalized.carbon} />
                  ) : null}
                </div>
              </div>
            ) : null}
            <EstimateDetails estimate={result.estimate} />
          </>
        ) : result.error ? (
          <div className="rounded-[var(--radius-console)] border border-danger/40 bg-danger/5 px-3 py-2">
            <p className="text-sm text-foreground">{result.error.message}</p>
            <p className="mt-1 font-mono text-xs text-muted-foreground">
              {result.error.code} · Request ID: {result.error.request_id}
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function NormalizedMetric({
  label,
  metric,
}: {
  label: string;
  metric: { status: string; min: number | null; max: number | null; unit: string };
}) {
  const hasRange = metric.status !== "insufficient_data" && metric.min != null && metric.max != null;
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      {hasRange ? (
        <p className="text-sm font-medium tabular-nums">
          {formatRange(metric.min as number, metric.max as number)}{" "}
          <span className="text-xs font-normal text-muted-foreground">{metric.unit}</span>
        </p>
      ) : (
        <p className="text-sm font-medium text-muted-foreground">Insufficient data</p>
      )}
      <MetricStatusBadge status={metric.status} />
    </div>
  );
}
