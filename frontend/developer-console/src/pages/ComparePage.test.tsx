import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComparePage } from "@/pages/ComparePage";
import { connectSession, mockApi, renderWithProviders } from "@/test/utils";

const RAW_KEY = "afp_live_orgcr-connected-secret-material";

function estimate(overrides: Record<string, unknown> = {}) {
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

function fillCandidates() {
  const providerInputs = screen.getAllByLabelText("Provider");
  const modelInputs = screen.getAllByLabelText("Model");
  fireEvent.change(providerInputs[0], { target: { value: "openai" } });
  fireEvent.change(modelInputs[0], { target: { value: "model-a" } });
  fireEvent.change(providerInputs[1], { target: { value: "anthropic" } });
  fireEvent.change(modelInputs[1], { target: { value: "model-b" } });
}

describe("ComparePage", () => {
  it("renders candidates independently, in the exact order returned, with no ranking", async () => {
    connectSession(RAW_KEY);
    mockApi([
      {
        method: "POST",
        path: "/v1/compare",
        body: {
          comparison_id: "cmp_1",
          modality: "text",
          activity_type: "text_generation",
          results: [
            {
              candidate: { provider: "openai", model: "model-a", model_version: null },
              status: "success",
              resolved: { provider: "openai", model: "model-a", model_version: "2026-01-01" },
              estimate: estimate({ estimate_id: "est_a" }),
              normalized: null,
              error: null,
            },
            {
              candidate: { provider: "anthropic", model: "model-b", model_version: null },
              status: "success",
              resolved: { provider: "anthropic", model: "model-b", model_version: "2026-02-01" },
              estimate: estimate({ estimate_id: "est_b" }),
              normalized: null,
              error: null,
            },
          ],
        },
      },
    ]);
    renderWithProviders(<ComparePage />);

    fillCandidates();
    fireEvent.click(screen.getByRole("button", { name: /run comparison/i }));

    await screen.findByText(/openai \/ model-a/);
    const cards = screen.getAllByText(/^Candidate \d$/);
    expect(cards).toHaveLength(2);
    // First result returned by the API (openai) must render first, even
    // though "anthropic" would sort first alphabetically — proving the
    // API's own order wins, not an inferred or convenient ordering.
    const bodyText = document.body.textContent ?? "";
    expect(bodyText.indexOf("openai / model-a")).toBeLessThan(bodyText.indexOf("anthropic"));

    // No ranking/winner/score vocabulary anywhere in the *result* cards
    // themselves (the page's own disclaimer text legitimately contains
    // the word "winner" — to explain that Compare never produces one —
    // so this scan is scoped to the rendered results, not the whole page).
    const resultsSection = screen.getByTestId("compare-results");
    for (const forbidden of ["Winner", "Best", "Recommended", "Score", "Rank", "#1"]) {
      expect(within(resultsSection).queryByText(new RegExp(forbidden, "i"))).not.toBeInTheDocument();
    }
  });

  it("shows the resolved model/version distinctly from the requested candidate", async () => {
    connectSession(RAW_KEY);
    mockApi([
      {
        method: "POST",
        path: "/v1/compare",
        body: {
          comparison_id: "cmp_1",
          modality: "text",
          activity_type: "text_generation",
          results: [
            {
              candidate: { provider: "openai", model: "model-a", model_version: null },
              status: "success",
              resolved: { provider: "openai", model: "model-a", model_version: "2026-01-01" },
              estimate: estimate(),
              normalized: null,
              error: null,
            },
          ],
        },
      },
    ]);
    renderWithProviders(<ComparePage />);
    fillCandidates();
    fireEvent.click(screen.getByRole("button", { name: /run comparison/i }));

    await screen.findByText("@ 2026-01-01");
  });

  it("preserves min/max ranges without collapsing them into a single value", async () => {
    connectSession(RAW_KEY);
    mockApi([
      {
        method: "POST",
        path: "/v1/compare",
        body: {
          comparison_id: "cmp_1",
          modality: "text",
          activity_type: "text_generation",
          results: [
            {
              candidate: { provider: "openai", model: "model-a", model_version: null },
              status: "success",
              resolved: { provider: "openai", model: "model-a", model_version: "2026-01-01" },
              estimate: estimate(),
              normalized: null,
              error: null,
            },
          ],
        },
      },
    ]);
    renderWithProviders(<ComparePage />);
    fillCandidates();
    fireEvent.click(screen.getByRole("button", { name: /run comparison/i }));

    expect(await screen.findByText(/0\.31.*0\.42/)).toBeInTheDocument();
  });

  it("shows a failed/insufficient-data candidate explicitly rather than hiding it", async () => {
    connectSession(RAW_KEY);
    mockApi([
      {
        method: "POST",
        path: "/v1/compare",
        body: {
          comparison_id: "cmp_1",
          modality: "text",
          activity_type: "text_generation",
          results: [
            {
              candidate: { provider: "openai", model: "model-a", model_version: null },
              status: "success",
              resolved: { provider: "openai", model: "model-a", model_version: "2026-01-01" },
              estimate: estimate(),
              normalized: null,
              error: null,
            },
            {
              candidate: { provider: "anthropic", model: "unknown-model", model_version: null },
              status: "failed",
              resolved: null,
              estimate: null,
              normalized: null,
              error: {
                code: "MODEL_NOT_FOUND",
                message: "Model 'unknown-model' was not found for provider 'anthropic'.",
                request_id: "req_abc",
              },
            },
          ],
        },
      },
    ]);
    renderWithProviders(<ComparePage />);
    fillCandidates();
    fireEvent.click(screen.getByRole("button", { name: /run comparison/i }));

    await screen.findByText(/Model 'unknown-model' was not found/);
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText(/req_abc/)).toBeInTheDocument();
  });

  it("sends the exact submitted candidate list to POST /v1/compare", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi([
      {
        method: "POST",
        path: "/v1/compare",
        body: { comparison_id: "cmp_1", modality: "text", activity_type: "text_generation", results: [] },
      },
    ]);
    renderWithProviders(<ComparePage />);
    fillCandidates();
    fireEvent.click(screen.getByRole("button", { name: /run comparison/i }));

    await waitFor(() => {
      const post = calls.find((c) => c.method === "POST");
      expect(post).toBeDefined();
      expect(post?.body).toMatchObject({
        modality: "text",
        activity_type: "text_generation",
        candidates: [
          { provider: "openai", model: "model-a" },
          { provider: "anthropic", model: "model-b" },
        ],
      });
    });
  });
});
