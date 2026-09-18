import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MetricRangeDisplay, ResourceRangesGrid } from "@/components/resource/MetricRangeDisplay";
import type { AggregateMetricRange } from "@/types/api";

describe("MetricRangeDisplay", () => {
  it("renders a min-max range, never a collapsed average", () => {
    render(
      <MetricRangeDisplay
        label="Energy"
        range={{ status: "ok", min: 42.8, max: 51.2, unit: "Wh" }}
      />,
    );
    expect(screen.getByText(/42\.8.*51\.2/)).toBeInTheDocument();
    expect(screen.getByText("Wh")).toBeInTheDocument();
    // The average of 42.8 and 51.2 is 47 - it must never appear as if it
    // were the reported value.
    expect(screen.queryByText(/^47(\s|$)/)).not.toBeInTheDocument();
  });

  it("shows 'Insufficient data' rather than 0 or N/A when status is insufficient_data", () => {
    render(
      <MetricRangeDisplay
        label="Energy"
        range={{ status: "insufficient_data", min: null, max: null, unit: "Wh" }}
      />,
    );
    expect(screen.getAllByText("Insufficient data").length).toBeGreaterThan(0);
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(screen.queryByText("N/A")).not.toBeInTheDocument();
  });

  it("shows 'Insufficient data' when min/max are null even if status is not insufficient_data", () => {
    render(
      <MetricRangeDisplay label="Energy" range={{ status: "ok", min: null, max: null, unit: "Wh" }} />,
    );
    expect(screen.getByText("Insufficient data")).toBeInTheDocument();
  });

  it("still renders the range for a partial aggregate, with an explicit Partial badge", () => {
    render(
      <MetricRangeDisplay
        label="Energy"
        range={{
          status: "partial",
          min: 10,
          max: 20,
          unit: "Wh",
          total_workloads: 100,
          measured_workloads: 60,
        }}
      />,
    );
    expect(screen.getByText(/10.*20/)).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByText(/60 of 100 workloads measured/)).toBeInTheDocument();
  });

  it("renders a single value (not a dash range) when min equals max", () => {
    render(<MetricRangeDisplay label="Energy" range={{ status: "ok", min: 5, max: 5, unit: "Wh" }} />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("ResourceRangesGrid renders all three metrics independently", () => {
    const range: AggregateMetricRange = {
      status: "ok",
      min: 1,
      max: 2,
      unit: "Wh",
      total_workloads: 10,
      measured_workloads: 10,
    };
    render(<ResourceRangesGrid energy={range} water={range} carbon={range} />);
    expect(screen.getByText("Energy")).toBeInTheDocument();
    expect(screen.getByText("Water")).toBeInTheDocument();
    expect(screen.getByText("Carbon")).toBeInTheDocument();
  });
});
