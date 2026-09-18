import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BenchmarksPage } from "@/pages/BenchmarksPage";
import { connectSession, mockApi, renderWithProviders } from "@/test/utils";

const RAW_KEY = "afp_live_orgcr-connected-secret-material";

describe("BenchmarksPage", () => {
  it("lists available benchmark definitions", async () => {
    connectSession(RAW_KEY);
    mockApi([
      {
        path: "/v1/benchmarks",
        body: {
          items: [
            {
              benchmark_id: "text_generation_standard",
              version: "1.0",
              name: "Standard text generation",
              description: "A representative conversational text-generation exchange.",
              activity_type: "text_generation",
              modality: "text",
              parameters: { input_tokens: 500, output_tokens: 500 },
            },
          ],
          total: 1,
        },
      },
    ]);
    renderWithProviders(<BenchmarksPage />);

    expect(await screen.findByText("Standard text generation")).toBeInTheDocument();
    expect(screen.getByText("text_generation")).toBeInTheDocument();
  });

  it("this is not a leaderboard: no ranking vocabulary in the list view", async () => {
    connectSession(RAW_KEY);
    mockApi([
      {
        path: "/v1/benchmarks",
        body: {
          items: [
            {
              benchmark_id: "b1",
              version: "1.0",
              name: "Benchmark One",
              description: "Description one.",
              activity_type: "text_generation",
              modality: "text",
              parameters: {},
            },
          ],
          total: 1,
        },
      },
    ]);
    renderWithProviders(<BenchmarksPage />);
    await screen.findByText("Benchmark One");

    for (const forbidden of ["Winner", "Best", "#1", "Score"]) {
      expect(screen.queryByText(new RegExp(forbidden, "i"))).not.toBeInTheDocument();
    }
  });
});
