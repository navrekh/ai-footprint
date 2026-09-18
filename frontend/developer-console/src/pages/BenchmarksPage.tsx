import { useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { Table, TableWrapper, Td, Th } from "@/components/ui/table";
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
        <TableWrapper>
          <Table>
            <caption className="sr-only">Available benchmark definitions</caption>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Activity type</Th>
                <Th>Modality</Th>
                <Th>Version</Th>
              </tr>
            </thead>
            <tbody>
              {benchmarks.data.items.map((benchmark) => (
                <tr key={benchmark.benchmark_id} className="last:[&>td]:border-b-0">
                  <Td>
                    <Link
                      to={`/benchmarks/${benchmark.benchmark_id}`}
                      className="font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {benchmark.name}
                    </Link>
                    <p className="mt-0.5 max-w-md truncate text-xs text-muted-foreground">
                      {benchmark.description}
                    </p>
                  </Td>
                  <Td className="text-muted-foreground">{benchmark.activity_type}</Td>
                  <Td className="text-muted-foreground">{benchmark.modality}</Td>
                  <Td className="font-mono text-xs text-muted-foreground">{benchmark.version}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </TableWrapper>
      )}
    </div>
  );
}
