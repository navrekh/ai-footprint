import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EstimateDetails } from "@/components/resource/EstimateDetails";
import { mockApi } from "@/test/utils";
import type { EstimateResponse } from "@/types/api";

function estimate(overrides: Partial<EstimateResponse> = {}): EstimateResponse {
  return {
    estimate_id: "est_1",
    energy: { status: "ok", min: 0.31, max: 0.42, unit: "Wh" },
    water: { status: "ok", min: 0.28, max: 0.35, unit: "mL" },
    carbon: { status: "ok", min: 0.04, max: 0.06, unit: "gCO2e" },
    confidence: "medium",
    evidence_level: 3,
    accounting_boundary: "B",
    methodology_version: "0.1",
    assumptions: ["Location-based grid emissions factor."],
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("EstimateDetails (compare/benchmark contract boundary)", () => {
  it("renders only fields present on the estimate response: confidence, evidence level, accounting boundary, methodology version, assumptions", () => {
    render(<EstimateDetails estimate={estimate()} />);

    expect(screen.getByText("medium")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("0.1")).toBeInTheDocument();
    expect(screen.getByText("Location-based grid emissions factor.")).toBeInTheDocument();
  });

  it("never fetches the separate methodology registry and never renders a Limitations or Sources section", () => {
    // If this component made any network call, mockApi's unmatched-route
    // 404 fallback would still resolve, so the absence of a call is the
    // real assertion here.
    const calls = mockApi([]);
    render(<EstimateDetails estimate={estimate()} />);

    expect(calls.some((c) => c.url.includes("/v1/methodology"))).toBe(false);
    expect(screen.queryByText("Limitations")).not.toBeInTheDocument();
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();
  });

  it("explains, rather than silently omits, why limitations/provenance are absent", () => {
    render(<EstimateDetails estimate={estimate()} />);

    expect(
      screen.getByText(/Limitations and source provenance are not included in this response/),
    ).toBeInTheDocument();
  });
});
