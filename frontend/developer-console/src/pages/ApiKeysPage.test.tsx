import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiKeysPage } from "@/pages/ApiKeysPage";
import { connectSession, mockApi, renderWithProviders } from "@/test/utils";
import type { ApiKey, Project } from "@/types/api";

const RAW_ORG_KEY = "afp_live_orgcr-connected-secret-material";
const RAW_PROJECT_KEY = "afp_live_proj1-connected-secret-material";

const PROJECTS: Project[] = [
  {
    id: "proj_1",
    organization_id: "org_1",
    name: "Web Frontend",
    slug: "web-frontend",
    description: null,
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "proj_2",
    organization_id: "org_1",
    name: "Mobile",
    slug: "mobile",
    description: null,
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

function keyMetadata(overrides: Partial<ApiKey>): ApiKey {
  return {
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
    ...overrides,
  };
}

function routesFor(connected: ApiKey) {
  return [
    { path: "/v1/api-keys", body: { items: [connected], total: 1 } },
    { path: "/v1/projects", body: { items: PROJECTS, total: PROJECTS.length } },
    {
      method: "POST",
      path: "/v1/api-keys",
      body: {
        id: "key_new",
        key: "afp_live_brandnew-one-time-secret",
        key_prefix: "afp_live_brandnew",
        name: "created",
      },
    },
  ];
}

async function openCreateDialog() {
  fireEvent.click(screen.getByRole("button", { name: /create api key/i }));
  return screen.findByRole("dialog");
}

function fillNameAndSubmit(dialog: HTMLElement) {
  fireEvent.change(within(dialog).getByLabelText(/name/i), {
    target: { value: "CI deploy key" },
  });
  fireEvent.click(within(dialog).getByRole("button", { name: /create api key/i }));
}

describe("API key creation scope (Fix 1)", () => {
  it("organization-level key: explicit project selection creates a project-scoped key", async () => {
    connectSession(RAW_ORG_KEY);
    const calls = mockApi(routesFor(keyMetadata({ project_id: null })));
    renderWithProviders(<ApiKeysPage />);

    await screen.findByText("Connected console key");
    const dialog = await openCreateDialog();

    const scopeSelect = within(dialog).getByRole("combobox");
    expect(within(scopeSelect).getByRole("option", { name: "Organization-level" })).toBeInTheDocument();
    fireEvent.change(scopeSelect, { target: { value: "proj_2" } });

    fillNameAndSubmit(dialog);
    await waitFor(() => {
      const post = calls.find((c) => c.method === "POST");
      expect(post).toBeDefined();
      expect(post?.body).toMatchObject({ name: "CI deploy key", project_id: "proj_2" });
    });
  });

  it("organization-level key: choosing Organization-level sends project_id = null", async () => {
    connectSession(RAW_ORG_KEY);
    const calls = mockApi(routesFor(keyMetadata({ project_id: null })));
    renderWithProviders(<ApiKeysPage />);

    await screen.findByText("Connected console key");
    const dialog = await openCreateDialog();
    fireEvent.change(within(dialog).getByRole("combobox"), { target: { value: "" } });

    fillNameAndSubmit(dialog);
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({ project_id: null });
    });
  });

  it("project-scoped key: scope is locked to the key's own project, no choice shown", async () => {
    connectSession(RAW_PROJECT_KEY);
    const calls = mockApi(
      routesFor(
        keyMetadata({ project_id: "proj_1", key_prefix: "afp_live_proj1" }),
      ),
    );
    renderWithProviders(<ApiKeysPage />);

    await screen.findByText("Connected console key");
    const dialog = await openCreateDialog();

    expect(within(dialog).queryByRole("combobox")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("Organization-level")).not.toBeInTheDocument();
    expect(within(dialog).getByDisplayValue("Web Frontend")).toBeDisabled();

    fillNameAndSubmit(dialog);
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({ project_id: "proj_1" });
    });
  });

  it("unknown scope: no organization-level option, explicit project required before submit", async () => {
    connectSession(RAW_ORG_KEY);
    // Connected key cannot be matched to any metadata row -> scope unknown.
    const calls = mockApi(
      routesFor(keyMetadata({ key_prefix: "afp_live_unrel" })),
    );
    renderWithProviders(<ApiKeysPage />);

    await screen.findByText("Connected console key");
    const dialog = await openCreateDialog();

    const scopeSelect = within(dialog).getByRole("combobox");
    expect(within(scopeSelect).queryByRole("option", { name: "Organization-level" })).toBeNull();
    expect(
      within(dialog).getByText(/could not determine the connected key's scope/i),
    ).toBeInTheDocument();

    fireEvent.change(within(dialog).getByLabelText(/name/i), {
      target: { value: "CI deploy key" },
    });
    const submit = within(dialog).getByRole("button", { name: /create api key/i });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(calls.find((c) => c.method === "POST")).toBeUndefined();

    fireEvent.change(scopeSelect, { target: { value: "proj_1" } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({ project_id: "proj_1" });
    });
  });

  it("never renders the connected raw API key anywhere in the UI", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(routesFor(keyMetadata({ project_id: null })));
    renderWithProviders(<ApiKeysPage />);

    await screen.findByText("Connected console key");
    const dialog = await openCreateDialog();
    fillNameAndSubmit(dialog);

    // The newly created key is shown exactly once (per contract)...
    await screen.findByText("afp_live_brandnew-one-time-secret");
    // ...but the connected credential's raw material never is.
    expect(document.body.innerHTML).not.toContain(RAW_ORG_KEY);
    expect(document.body.innerHTML).not.toContain("connected-secret-material");
  });
});
