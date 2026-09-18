import { ComingSoon } from "@/components/ComingSoon";

export function UsagePage() {
  return (
    <ComingSoon
      title="Usage"
      description="Estimated resource impact of recorded workloads, aggregated over time."
      capabilities={[
        "Estimated ranges for energy, water and CO₂e, never single exact values",
        "Confidence, coverage and measurement status alongside every range",
        "Methodology version and provenance for each aggregate",
      ]}
    />
  );
}

export function ComparePage() {
  return (
    <ComingSoon
      title="Compare"
      description="Side-by-side estimated resource impact for different workload configurations."
      capabilities={[
        "Compare estimated ranges, not scores or rankings",
        "Assumptions and coverage shown for every compared scenario",
        "No recommendation, winner or efficiency verdict is produced",
      ]}
    />
  );
}

export function BenchmarksPage() {
  return (
    <ComingSoon
      title="Benchmarks"
      description="Published reference estimates from the AI Footprint methodology."
      capabilities={[
        "Reference estimated ranges with their evidence level",
        "Methodology version and source provenance",
        "Coverage notes describing what a benchmark does and does not include",
      ]}
    />
  );
}

export function ApiExplorerPage() {
  return (
    <ComingSoon
      title="API Explorer"
      description="Issue authenticated requests against the AI Footprint REST API from the console."
      capabilities={[
        "Requests sent with the key already held in this browser session",
        "Raw request and response bodies, including request IDs",
        "No key material written to URLs, history or logs",
      ]}
    />
  );
}

export function DocumentationPage() {
  return (
    <ComingSoon
      title="Documentation"
      description="Reference material for the API, SDK and estimation methodology."
      capabilities={[
        "Quick start and authentication reference",
        "Endpoint reference generated from the OpenAPI contract",
        "Methodology, assumptions and provenance documentation",
      ]}
    />
  );
}
