import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";

import { ErrorState } from "@/components/ErrorState";
import { InlineError } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { CandidateListEditor, MIN_CANDIDATES } from "@/components/resource/CandidateListEditor";
import { ComparisonResultCard } from "@/components/resource/ComparisonResultCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBenchmark, useRunBenchmark } from "@/hooks/queries";
import type { ComparisonCandidate } from "@/types/api";

export function BenchmarkDetailPage() {
  const { benchmarkId } = useParams<{ benchmarkId: string }>();
  const benchmark = useBenchmark(benchmarkId);
  const [candidates, setCandidates] = useState<ComparisonCandidate[]>([
    { provider: "", model: "", model_version: "" },
    { provider: "", model: "", model_version: "" },
  ]);
  const run = useRunBenchmark();

  const canRun =
    candidates.length >= MIN_CANDIDATES &&
    candidates.every((c) => c.provider.trim() && c.model.trim()) &&
    !run.isPending;

  function handleRun() {
    if (!canRun || !benchmarkId) return;
    run.mutate({
      benchmark_id: benchmarkId,
      candidates: candidates.map((c) => ({
        provider: c.provider.trim(),
        model: c.model.trim(),
        model_version: c.model_version?.trim() || undefined,
      })),
    });
  }

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/benchmarks">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to benchmarks
        </Link>
      </Button>

      {benchmark.isPending ? (
        <Skeleton className="h-8 w-64" />
      ) : benchmark.error ? (
        <ErrorState error={benchmark.error} onRetry={() => benchmark.refetch()} />
      ) : (
        <>
          <PageHeader title={benchmark.data.name} description={benchmark.data.description} />

          <Card>
            <CardHeader>
              <CardTitle>Definition</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                    Benchmark ID
                  </dt>
                  <dd className="mt-1 font-mono text-xs">{benchmark.data.benchmark_id}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                    Version
                  </dt>
                  <dd className="mt-1 font-mono text-sm">{benchmark.data.version}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                    Activity type
                  </dt>
                  <dd className="mt-1 text-sm">{benchmark.data.activity_type}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                    Modality
                  </dt>
                  <dd className="mt-1 text-sm">{benchmark.data.modality}</dd>
                </div>
              </dl>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Workload parameters
                </p>
                <dl className="mt-1 grid gap-2 sm:grid-cols-3">
                  {Object.entries(benchmark.data.parameters).map(([key, value]) => (
                    <div key={key} className="rounded border border-border px-3 py-2">
                      <dt className="font-mono text-xs text-muted-foreground">{key}</dt>
                      <dd className="text-sm font-medium">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Run this benchmark</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Evaluates the fixed workload above independently against each candidate — exactly
                like Compare. This produces a measurement view, not a leaderboard: results are
                shown in the order submitted, with no score, ranking, or winner.
              </p>
              <CandidateListEditor candidates={candidates} onChange={setCandidates} />
              <InlineError error={run.error} />
              <Button onClick={handleRun} disabled={!canRun}>
                {run.isPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
                Run benchmark
              </Button>
            </CardContent>
          </Card>

          {run.data ? (
            <div className="space-y-4">
              <p className="text-xs text-muted-foreground">
                Benchmark version: <span className="font-mono">{run.data.benchmark_version}</span>{" "}
                — results below are shown in the exact order submitted.
              </p>
              {run.data.results.map((result, index) => (
                <ComparisonResultCard key={index} result={result} index={index} />
              ))}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
