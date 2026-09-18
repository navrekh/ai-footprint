import { useState } from "react";
import { RefreshCw } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { MetricRangeDisplay, ResourceRangesGrid } from "@/components/resource/MetricRangeDisplay";
import { UsageTrend } from "@/components/resource/UsageTrend";
import { WorkloadCoverage } from "@/components/resource/WorkloadCoverage";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/field";
import { CardsSkeleton, TableSkeleton } from "@/components/ui/skeleton";
import { Table, TableWrapper, Td, Th } from "@/components/ui/table";
import {
  useApplications,
  useProjects,
  useUsageByActivity,
  useUsageByApplication,
  useUsageByModel,
  useUsageByProvider,
  useUsageSummary,
  useUsageTimeseries,
} from "@/hooks/queries";
import { formatDateTime } from "@/lib/utils/format";
import type { AggregateMetricRange, UsageFilterParams, UsageGranularity } from "@/types/api";

const ACTIVITY_TYPES = [
  "text_generation",
  "text_reasoning",
  "image_generation",
  "image_editing",
  "image_enhancement",
  "video_generation",
  "audio_generation",
  "speech_to_text",
  "vision",
  "code_generation",
  "code_review",
  "debugging",
  "test_generation",
  "code_refactoring",
  "coding_agent",
  "embedding",
  "rag",
  "classification",
  "agent_workflow",
];

type BreakdownDimension = "provider" | "model" | "activity" | "application";

/** datetime-local's value has no timezone; interpreted as local time, then
 * converted to a UTC ISO string — the same pattern already used for API key
 * expiry in ApiKeysPage.tsx. Empty means "let the backend apply its own
 * default," never a client-invented default. */
function toIsoOrUndefined(localValue: string): string | undefined {
  if (!localValue) return undefined;
  const date = new Date(localValue);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

export function UsagePage() {
  const [fromLocal, setFromLocal] = useState("");
  const [toLocal, setToLocal] = useState("");
  const [projectId, setProjectId] = useState("");
  const [applicationId, setApplicationId] = useState("");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [activityType, setActivityType] = useState("");
  const [dimension, setDimension] = useState<BreakdownDimension>("provider");
  const [granularity, setGranularity] = useState<UsageGranularity>("day");

  const projects = useProjects();
  const applications = useApplications();

  const filters: UsageFilterParams = {
    from: toIsoOrUndefined(fromLocal),
    to: toIsoOrUndefined(toLocal),
    project: projectId || undefined,
    application: applicationId || undefined,
    provider: provider || undefined,
    model: model || undefined,
    activity_type: activityType || undefined,
  };

  const summary = useUsageSummary(filters);
  // Only the currently selected breakdown dimension is fetched — switching
  // tabs fetches on demand rather than issuing all four requests upfront.
  const byProvider = useUsageByProvider(filters, { limit: 50 }, dimension === "provider");
  const byModel = useUsageByModel(filters, { limit: 50 }, dimension === "model");
  const byActivity = useUsageByActivity(filters, { limit: 50 }, dimension === "activity");
  const byApplication = useUsageByApplication(
    filters,
    { limit: 50 },
    dimension === "application",
  );
  const timeseries = useUsageTimeseries(filters, granularity);

  const activeBreakdown =
    dimension === "provider"
      ? byProvider
      : dimension === "model"
        ? byModel
        : dimension === "activity"
          ? byActivity
          : byApplication;
  const isRefreshing = summary.isFetching || activeBreakdown.isFetching || timeseries.isFetching;

  function refreshUsage() {
    void Promise.all([summary.refetch(), activeBreakdown.refetch(), timeseries.refetch()]);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Usage & Resource Impact"
        description="Understand workload volume, measurement coverage, and estimated energy, water, and carbon ranges from persisted workload events."
        actions={
          <Button variant="secondary" size="sm" onClick={refreshUsage} disabled={isRefreshing}>
            <RefreshCw className={isRefreshing ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
            Refresh
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="From" htmlFor="usage-from" hint="Inclusive. Defaults to 30 days before To.">
            <Input
              id="usage-from"
              type="datetime-local"
              value={fromLocal}
              onChange={(event) => setFromLocal(event.target.value)}
            />
          </Field>
          <Field label="To" htmlFor="usage-to" hint="Exclusive. Defaults to now.">
            <Input
              id="usage-to"
              type="datetime-local"
              value={toLocal}
              onChange={(event) => setToLocal(event.target.value)}
            />
          </Field>
          <Field label="Project" htmlFor="usage-project">
            <Select
              id="usage-project"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
            >
              <option value="">All projects</option>
              {projects.data?.items.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field
            label="Application"
            htmlFor="usage-application"
            hint={
              dimension === "application"
                ? 'Not applicable when viewing usage by application: that breakdown always groups every application.'
                : undefined
            }
          >
            <Select
              id="usage-application"
              value={applicationId}
              disabled={dimension === "application"}
              onChange={(event) => setApplicationId(event.target.value)}
            >
              <option value="">All applications</option>
              {applications.data?.items.map((application) => (
                <option key={application.id} value={application.id}>
                  {application.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Provider" htmlFor="usage-provider" hint="Optional.">
            <Input
              id="usage-provider"
              value={provider}
              placeholder="openai"
              onChange={(event) => setProvider(event.target.value)}
            />
          </Field>
          <Field label="Model" htmlFor="usage-model" hint="Optional.">
            <Input
              id="usage-model"
              value={model}
              placeholder="model-id"
              onChange={(event) => setModel(event.target.value)}
            />
          </Field>
          <Field label="Activity type" htmlFor="usage-activity">
            <Select
              id="usage-activity"
              value={activityType}
              onChange={(event) => setActivityType(event.target.value)}
            >
              <option value="">All activity types</option>
              {ACTIVITY_TYPES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </Select>
          </Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {summary.isPending ? (
            <CardsSkeleton count={5} />
          ) : summary.error ? (
            <ErrorState error={summary.error} onRetry={() => summary.refetch()} />
          ) : summary.data.workloads.total === 0 ? (
            <EmptyState
              title="No workloads yet"
              description="Connect your application and send your first AI workload to begin measuring resource impact."
            />
          ) : (
            <>
              <p className="text-xs text-muted-foreground">
                Period: {formatDateTime(summary.data.period.from)} –{" "}
                {formatDateTime(summary.data.period.to)}
              </p>
              <WorkloadCoverage counts={summary.data.workloads} />
              <ResourceRangesGrid
                energy={summary.data.energy}
                water={summary.data.water}
                carbon={summary.data.carbon}
              />
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
          <CardTitle>Breakdown</CardTitle>
          <div className="max-w-[200px]">
            <Select
              aria-label="Breakdown dimension"
              value={dimension}
              onChange={(event) => setDimension(event.target.value as BreakdownDimension)}
            >
              <option value="provider">By provider</option>
              <option value="model">By model</option>
              <option value="activity">By activity</option>
              <option value="application">By application</option>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {dimension === "application" ? (
            <p className="mb-3 text-xs text-muted-foreground">
              This breakdown groups every application in the selected period; the Application
              filter above does not constrain it.
            </p>
          ) : null}
          {activeBreakdown.isPending ? (
            <TableSkeleton rows={4} columns={5} />
          ) : activeBreakdown.error ? (
            <ErrorState error={activeBreakdown.error} onRetry={() => activeBreakdown.refetch()} />
          ) : activeBreakdown.data.items.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No workloads matched this period and these filters.
            </p>
          ) : (
            <TableWrapper>
              <Table>
                <caption className="sr-only">Usage by {dimension}</caption>
                <thead>
                  <tr>
                    <Th>{dimension === "application" ? "Application" : dimension}</Th>
                    <Th>Coverage</Th>
                    <Th>Energy</Th>
                    <Th>Water</Th>
                    <Th>Carbon</Th>
                  </tr>
                </thead>
                <tbody>
                  {dimension === "provider" &&
                    byProvider.data?.items.map((item) => (
                      <tr key={item.provider} className="last:[&>td]:border-b-0">
                        <Td className="font-medium">{item.provider}</Td>
                        <BreakdownCells counts={item.workloads} {...item} />
                      </tr>
                    ))}
                  {dimension === "model" &&
                    byModel.data?.items.map((item) => (
                      <tr
                        key={`${item.provider}/${item.model}/${item.model_version ?? ""}`}
                        className="last:[&>td]:border-b-0"
                      >
                        <Td>
                          <span className="font-medium">
                            {item.provider}/{item.model}
                          </span>
                          {item.model_version ? (
                            <p className="font-mono text-xs text-muted-foreground">
                              {item.model_version}
                            </p>
                          ) : null}
                        </Td>
                        <BreakdownCells counts={item.workloads} {...item} />
                      </tr>
                    ))}
                  {dimension === "activity" &&
                    byActivity.data?.items.map((item) => (
                      <tr key={item.activity_type} className="last:[&>td]:border-b-0">
                        <Td className="font-medium">{item.activity_type}</Td>
                        <BreakdownCells counts={item.workloads} {...item} />
                      </tr>
                    ))}
                  {dimension === "application" &&
                    byApplication.data?.items.map((item) => (
                      <tr key={item.application_id} className="last:[&>td]:border-b-0">
                        <Td className="font-medium">{item.application_name}</Td>
                        <BreakdownCells counts={item.workloads} {...item} />
                      </tr>
                    ))}
                </tbody>
              </Table>
            </TableWrapper>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
          <CardTitle>Time series</CardTitle>
          <div className="max-w-[160px]">
            <Select
              aria-label="Granularity"
              value={granularity}
              onChange={(event) => setGranularity(event.target.value as UsageGranularity)}
            >
              <option value="day">Day</option>
              <option value="week">Week</option>
              <option value="month">Month</option>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {timeseries.isPending ? (
            <TableSkeleton rows={4} columns={5} />
          ) : timeseries.error ? (
            <ErrorState error={timeseries.error} onRetry={() => timeseries.refetch()} />
          ) : timeseries.data.items.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No workloads matched this period and these filters.
            </p>
          ) : (
            <div className="space-y-4">
              <UsageTrend points={timeseries.data.items} />
              <details>
                <summary className="cursor-pointer text-sm font-medium text-primary">
                  View complete data table
                </summary>
                <TableWrapper className="mt-3">
                  <Table>
                <caption className="sr-only">Usage over time, by {timeseries.data.granularity}</caption>
                <thead>
                  <tr>
                    <Th>Period start</Th>
                    <Th>Coverage</Th>
                    <Th>Energy</Th>
                    <Th>Water</Th>
                    <Th>Carbon</Th>
                  </tr>
                </thead>
                <tbody>
                  {timeseries.data.items.map((point) => (
                    <tr key={point.period_start} className="last:[&>td]:border-b-0">
                      <Td className="font-medium">{formatDateTime(point.period_start)}</Td>
                      <BreakdownCells counts={point.workloads} {...point} />
                    </tr>
                  ))}
                </tbody>
                  </Table>
                </TableWrapper>
              </details>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function BreakdownCells({
  counts,
  energy,
  water,
  carbon,
}: {
  counts: { total: number; measured: number; coverage_percent: number };
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}) {
  return (
    <>
      <Td className="text-muted-foreground">
        {counts.coverage_percent}% ({counts.measured.toLocaleString()}/{counts.total.toLocaleString()})
      </Td>
      <Td>
        <CompactRange range={energy} />
      </Td>
      <Td>
        <CompactRange range={water} />
      </Td>
      <Td>
        <CompactRange range={carbon} />
      </Td>
    </>
  );
}

function CompactRange({ range }: { range: AggregateMetricRange }) {
  return <MetricRangeDisplay range={range} showStatus={range.status !== "ok"} compact />;
}
