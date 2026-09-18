import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { Field, Select } from "@/components/ui/field";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useBenchmarks } from "@/hooks/queries";

const MODALITIES = ["text", "image", "video", "audio", "coding", "agent", "other"];

export function BenchmarksPage() {
  const [modality, setModality] = useState("");
  const benchmarks = useBenchmarks(undefined, modality || undefined);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Benchmarks"
        description="Standardized, versioned workload definitions maintained by AI Footprint. A benchmark is a reproducible measurement view, not a leaderboard — running one evaluates candidates independently, exactly like Compare."
      />

      <div className="max-w-xs">
        <Field label="Filter by modality" htmlFor="benchmark-modality-filter">
          <Select
            id="benchmark-modality-filter"
            value={modality}
            onChange={(event) => setModality(event.target.value)}
          >
            <option value="">All modalities</option>
            {MODALITIES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      {benchmarks.isPending ? (
        <TableSkeleton rows={4} columns={4} />
      ) : benchmarks.error ? (
        <ErrorState error={benchmarks.error} onRetry={() => benchmarks.refetch()} />
      ) : benchmarks.data.items.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          No benchmark definitions match this filter.
        </p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {benchmarks.data.items.map((benchmark) => (
            <Link
              key={benchmark.benchmark_id}
              to={`/benchmarks/${benchmark.benchmark_id}`}
              className="group grid min-w-0 grid-cols-[minmax(0,1fr)_auto] gap-4 rounded-[var(--radius-console)] border border-border bg-surface p-5 transition-colors hover:border-primary/50 hover:bg-surface-raised/40"
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-mono">v{benchmark.version}</span>
                  <span aria-hidden="true">·</span>
                  <span>{benchmark.modality}</span>
                  <span aria-hidden="true">·</span>
                  <span>{benchmark.activity_type}</span>
                </div>
                <h2 className="mt-2 font-semibold text-foreground group-hover:text-primary">{benchmark.name}</h2>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{benchmark.description}</p>
                <p className="mt-4 font-mono text-[11px] text-muted-foreground">{benchmark.benchmark_id}</p>
              </div>
              <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary" aria-hidden="true" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
