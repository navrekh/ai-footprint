import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { UsagePage } from "@/pages/UsagePage";
import { connectSession, mockApi, renderWithProviders, TEST_BASE_URL } from "@/test/utils";

const RAW_KEY = "afp_live_orgcr-connected-secret-material";

const PERIOD = { from: "2026-01-01T00:00:00Z", to: "2026-01-31T00:00:00Z" };
const SUMMARY_COUNTS = {
  total: 100,
  measured: 70,
  partial: 25,
  insufficient_data: 5,
  coverage_percent: 70,
};
const SUMMARY_RANGE = {
  status: "partial",
  min: 428.3,
  max: 512.7,
  unit: "Wh",
  total_workloads: 100,
  measured_workloads: 70,
};
const BREAKDOWN_COUNTS = {
  total: 40,
  measured: 40,
  partial: 0,
  insufficient_data: 0,
  coverage_percent: 100,
};
const BREAKDOWN_RANGE = {
  status: "ok",
  min: 11.1,
  max: 22.2,
  unit: "Wh",
  total_workloads: 40,
  measured_workloads: 40,
};
const TIMESERIES_COUNTS = {
  total: 9,
  measured: 9,
  partial: 0,
  insufficient_data: 0,
  coverage_percent: 100,
};
const TIMESERIES_RANGE = {
  status: "ok",
  min: 1.1,
  max: 2.2,
  unit: "Wh",
  total_workloads: 9,
  measured_workloads: 9,
};
const INSUFFICIENT_RANGE = {
  status: "insufficient_data",
  min: null,
  max: null,
  unit: "Wh",
  total_workloads: 100,
  measured_workloads: 0,
};

function baseRoutes() {
  return [
    { path: "/v1/projects", body: { items: [], total: 0 } },
    { path: "/v1/applications", body: { items: [], total: 0 } },
    {
      path: "/v1/usage/summary",
      body: {
        period: PERIOD,
        workloads: SUMMARY_COUNTS,
        energy: SUMMARY_RANGE,
        water: SUMMARY_RANGE,
        carbon: SUMMARY_RANGE,
      },
    },
    {
      path: "/v1/usage/by-provider",
      body: {
        period: PERIOD,
        items: [
          {
            provider: "openai",
            workloads: BREAKDOWN_COUNTS,
            energy: BREAKDOWN_RANGE,
            water: BREAKDOWN_RANGE,
            carbon: BREAKDOWN_RANGE,
          },
        ],
        total: 1,
      },
    },
    {
      path: "/v1/usage/timeseries",
      body: {
        period: PERIOD,
        granularity: "day",
        items: [
          {
            period_start: "2026-01-01T00:00:00Z",
            workloads: TIMESERIES_COUNTS,
            energy: TIMESERIES_RANGE,
            water: TIMESERIES_RANGE,
            carbon: TIMESERIES_RANGE,
          },
        ],
      },
    },
  ];
}

function summaryCard() {
  const heading = screen.getByText("Summary");
  return heading.closest("div")?.parentElement as HTMLElement;
}

describe("UsagePage", () => {
  it("renders summary as a range, with coverage, never a collapsed point value", async () => {
    connectSession(RAW_KEY);
    mockApi(baseRoutes());
    renderWithProviders(<UsagePage />);

    await screen.findByText("Summary");
    const card = within(summaryCard());
    expect((await card.findAllByText(/428\.3.*512\.7/)).length).toBeGreaterThan(0);
    expect(card.getByText("70%")).toBeInTheDocument();
    expect(card.getByText("70")).toBeInTheDocument();
    expect(card.getByText("25")).toBeInTheDocument();
    expect(card.getByText("5")).toBeInTheDocument();
  });

  it("shows the insufficient-data state explicitly, never as 0", async () => {
    connectSession(RAW_KEY);
    mockApi([
      ...baseRoutes().filter((r) => r.path !== "/v1/usage/summary"),
      {
        path: "/v1/usage/summary",
        body: {
          period: PERIOD,
          workloads: { total: 100, measured: 0, partial: 0, insufficient_data: 100, coverage_percent: 0 },
          energy: INSUFFICIENT_RANGE,
          water: INSUFFICIENT_RANGE,
          carbon: INSUFFICIENT_RANGE,
        },
      },
    ]);
    renderWithProviders(<UsagePage />);

    expect((await screen.findAllByText("Insufficient data")).length).toBeGreaterThan(0);
  });

  it("sends the selected date range as query parameters, not a client-invented default", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi(baseRoutes());
    renderWithProviders(<UsagePage />);
    await screen.findByText("Summary");

    fireEvent.change(screen.getByLabelText("From"), { target: { value: "2026-01-01T00:00" } });

    await waitFor(() => {
      const summaryCall = calls.find((c) => c.url.includes("/v1/usage/summary") && c.url.includes("from="));
      expect(summaryCall).toBeDefined();
    });
  });

  it("switches breakdown dimension and requests only that dimension", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi([
      ...baseRoutes(),
      {
        path: "/v1/usage/by-model",
        body: {
          period: PERIOD,
          items: [
            {
              provider: "openai",
              model: "model-id",
              model_version: "v1",
              workloads: BREAKDOWN_COUNTS,
              energy: BREAKDOWN_RANGE,
              water: BREAKDOWN_RANGE,
              carbon: BREAKDOWN_RANGE,
            },
          ],
          total: 1,
        },
      },
    ]);
    renderWithProviders(<UsagePage />);
    await screen.findByText("openai");
    expect(calls.some((c) => c.url.includes("/v1/usage/by-model"))).toBe(false);

    fireEvent.change(screen.getByLabelText("Breakdown dimension"), { target: { value: "model" } });
    await screen.findByText(/openai\/model-id/);

    expect(calls.some((c) => c.url.includes("/v1/usage/by-model"))).toBe(true);
  });

  it("supports day/week/month granularity for the time series", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi(baseRoutes());
    renderWithProviders(<UsagePage />);
    await screen.findByText("Summary");

    fireEvent.change(screen.getByLabelText("Granularity"), { target: { value: "week" } });

    await waitFor(() => {
      expect(calls.some((c) => c.url.includes("granularity=week"))).toBe(true);
    });
  });

  it("disables the Application filter and explains why once By application is selected, without sending it as a query parameter", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi([
      ...baseRoutes().filter((r) => r.path !== "/v1/applications"),
      {
        path: "/v1/applications",
        body: { items: [{ id: "app-1", name: "Application A" }], total: 1 },
      },
      {
        path: "/v1/usage/by-application",
        body: {
          period: PERIOD,
          items: [
            {
              application_id: "app-1",
              application_name: "Application A",
              workloads: BREAKDOWN_COUNTS,
              energy: BREAKDOWN_RANGE,
              water: BREAKDOWN_RANGE,
              carbon: BREAKDOWN_RANGE,
            },
          ],
          total: 1,
        },
      },
    ]);
    renderWithProviders(<UsagePage />);
    await screen.findByText("openai");

    // Normally available and enabled for the default (non-application) breakdown.
    const applicationSelect = screen.getByLabelText("Application") as HTMLSelectElement;
    expect(applicationSelect).not.toBeDisabled();
    await within(applicationSelect).findByText("Application A");

    fireEvent.change(applicationSelect, { target: { value: "app-1" } });
    fireEvent.change(screen.getByLabelText("Breakdown dimension"), {
      target: { value: "application" },
    });
    await screen.findByText("Application A");

    // Field is now visibly non-applicable, but the previous selection is preserved
    // (it still legitimately constrains Summary and Time series above).
    expect(applicationSelect).toBeDisabled();
    expect(applicationSelect.value).toBe("app-1");
    expect(
      screen.getByText('Not applicable when viewing usage by application: that breakdown always groups every application.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/This breakdown groups every application in the selected period/),
    ).toBeInTheDocument();

    // The actual request never carries the application filter, matching the backend contract.
    const byApplicationCall = calls.find((c) => c.url.includes("/v1/usage/by-application"));
    expect(byApplicationCall).toBeDefined();
    expect(byApplicationCall?.url).not.toContain("application=");
  });

  it("never sends the connected raw API key anywhere but the Authorization header", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi(baseRoutes());
    renderWithProviders(<UsagePage />);
    await screen.findByText("openai");
    await waitFor(() => expect(calls.length).toBeGreaterThanOrEqual(3));

    for (const call of calls) {
      expect(call.url).not.toContain(RAW_KEY);
      expect(call.url.startsWith(TEST_BASE_URL)).toBe(true);
    }
    expect(document.body.innerHTML).not.toContain(RAW_KEY);
  });
});
