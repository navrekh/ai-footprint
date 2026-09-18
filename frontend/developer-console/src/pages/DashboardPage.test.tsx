import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DashboardPage } from "@/pages/DashboardPage";
import { connectSession, mockApi, renderWithProviders } from "@/test/utils";
import type { ApiKey, Organization, Project } from "@/types/api";

const RAW_ORG_KEY = "afp_live_orgcr-connected-secret-material";

const ORGANIZATION: Organization = {
  id: "org_1",
  name: "Acme Sustainability",
  slug: "acme-sustainability",
  status: "active",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const CONNECTED_KEY: ApiKey = {
  id: "key_conn",
  organization_id: "org_1",
  project_id: null,
  key_prefix: "afp_live_orgcr",
  name: "Connected console key",
  status: "active",
  created_at: "2026-01-01T00:00:00Z",
  expires_at: null,
  last_used_at: null,
  revoked_at: null,
};

const PROJECT: Project = {
  id: "proj_1",
  organization_id: "org_1",
  name: "Web Frontend",
  slug: "web-frontend",
  description: null,
  status: "active",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function dashboardRoutes(projects: Project[], connected: ApiKey | null) {
  return [
    { path: "/v1/projects", body: { items: projects, total: projects.length } },
    { path: "/v1/applications", body: { items: [], total: 0 } },
    { path: "/v1/api-keys", body: { items: connected ? [connected] : [], total: connected ? 1 : 0 } },
    { path: "/v1/organizations/org_1", body: ORGANIZATION },
  ];
}

describe("Dashboard organization discovery (Fix 2)", () => {
  it("organization with projects: shows organization details", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(dashboardRoutes([PROJECT], CONNECTED_KEY));
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("Acme Sustainability")).toBeInTheDocument();
    expect(screen.getByText("acme-sustainability")).toBeInTheDocument();
  });

  it("organization with zero projects: still resolves via the connected key's metadata", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(dashboardRoutes([], CONNECTED_KEY));
    renderWithProviders(<DashboardPage />);

    // Regression: previously the org card was empty unless >= 1 project existed.
    expect(await screen.findByText("Acme Sustainability")).toBeInTheDocument();
    expect(screen.getByText("acme-sustainability")).toBeInTheDocument();
  });

  it("zero projects and unidentifiable key: explains the limitation instead of fabricating an ID", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(dashboardRoutes([], null));
    renderWithProviders(<DashboardPage />);

    expect(
      await screen.findByText(/does not fabricate organization identity/i),
    ).toBeInTheDocument();
    expect(screen.queryByText("Acme Sustainability")).not.toBeInTheDocument();
    expect(document.body.innerHTML).not.toContain(RAW_ORG_KEY);
  });
});
