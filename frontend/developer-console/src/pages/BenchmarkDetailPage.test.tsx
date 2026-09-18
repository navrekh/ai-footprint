import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { BenchmarkDetailPage } from "@/pages/BenchmarkDetailPage";
import { connectSession, mockApi } from "@/test/utils";

const RAW_KEY = "afp_live_orgcr-connected-secret-material";

function renderDetail(benchmarkId = "text_generation_standard") {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/benchmarks/${benchmarkId}`]}>
        <Routes>
          <Route path="/benchmarks/:benchmarkId" element={<BenchmarkDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const DEFINITION = {
  benchmark_id: "text_generation_standard",
  version: "1.0",
  name: "Standard text generation",
  description: "A representative conversational text-generation exchange.",
  activity_type: "text_generation",
  modality: "text",
  parameters: { input_tokens: 500, output_tokens: 500 },
};

function estimate() {
  return {
    estimate_id: "est_1",
    energy: { status: "ok", min: 0.08, max: 0.11, unit: "Wh" },
    water: { status: "ok", min: 0.07, max: 0.09, unit: "mL" },
    carbon: { status: "ok", min: 0.01, max: 0.015, unit: "gCO2e" },
    confidence: "medium",
    evidence_level: 3,
    accounting_boundary: "B",
    methodology_version: "0.1",
    assumptions: ["Location-based grid emissions factor."],
    created_at: "2026-01-01T00:00:00Z",
  };
}

describe("BenchmarkDetailPage", () => {
  it("loads and renders the benchmark definition, including parameters", async () => {
    connectSession(RAW_KEY);
    mockApi([{ path: "/v1/benchmarks/text_generation_standard", body: DEFINITION }]);
    renderDetail();

    expect(await screen.findByText("Standard text generation")).toBeInTheDocument();
    expect(screen.getByText("1.0")).toBeInTheDocument();
    expect(screen.getAllByText("500")).toHaveLength(2); // input_tokens and output_tokens
  });

  it("runs the benchmark and preserves methodology/normalization metadata in the result", async () => {
    connectSession(RAW_KEY);
    mockApi([
      { path: "/v1/benchmarks/text_generation_standard", body: DEFINITION },
      {
        method: "POST",
        path: "/v1/benchmarks/run",
        body: {
          benchmark_id: "text_generation_standard",
          benchmark_version: "1.0",
          modality: "text",
          activity_type: "text_generation",
          results: [
            {
              candidate: { provider: "openai", model: "model-a", model_version: null },
              status: "success",
              resolved: { provider: "openai", model: "model-a", model_version: "2026-01-01" },
              estimate: estimate(),
              normalized: {
                denominator: { value: 1, unit: "1K tokens", basis: "input_plus_output" },
                energy: {
                  status: "ok",
                  min: 0.08,
                  max: 0.11,
                  unit: "Wh per 1K tokens",
                  confidence: "medium",
                  evidence_level: 3,
                  methodology_version: "0.1",
                  accounting_boundary: "B",
                },
                water: null,
                carbon: null,
              },
              error: null,
            },
          ],
        },
      },
    ]);
    renderDetail();
    await screen.findByText("Standard text generation");

    fireEvent.change(screen.getAllByLabelText("Provider")[0], { target: { value: "openai" } });
    fireEvent.change(screen.getAllByLabelText("Model")[0], { target: { value: "model-a" } });
    fireEvent.change(screen.getAllByLabelText("Provider")[1], { target: { value: "anthropic" } });
    fireEvent.change(screen.getAllByLabelText("Model")[1], { target: { value: "model-b" } });
    fireEvent.click(screen.getByRole("button", { name: /run benchmark/i }));

    await screen.findByText(/Normalized/); // normalized section rendered
    // The raw estimate range and the normalized range are both present -
    // neither is dropped in favor of the other.
    await waitFor(() => {
      expect(screen.getAllByText(/0\.08.*0\.11/).length).toBe(2);
    });
  });
});
