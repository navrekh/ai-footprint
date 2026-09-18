import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApplicationFormDialog } from "@/components/ApplicationFormDialog";
import { connectSession, mockApi, renderWithProviders } from "@/test/utils";
import type { ApiKey, Application, Project } from "@/types/api";

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
      path: "/v1/applications",
      body: {
        id: "app_new",
        project_id: "proj_1",
        name: "created",
        slug: "created",
        description: null,
        status: "active",
        environment: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    },
  ];
}

function fillNameAndSubmit() {
  fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Support Bot" } });
  fireEvent.click(screen.getByRole("button", { name: /create application/i }));
}

describe("Application project scope (Fix 1)", () => {
  it("organization-level key: requires an explicit project, never an ambiguous default", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(routesFor(keyMetadata({ project_id: null })));
    renderWithProviders(<ApplicationFormDialog open onOpenChange={() => {}} />);

    await screen.findByLabelText("Project");
    expect(screen.queryByText(/use the api key'?s own project/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create application/i })).toBeDisabled();
  });

  it("organization-level key: explicit project selection sends that exact project_id", async () => {
    connectSession(RAW_ORG_KEY);
    const calls = mockApi(routesFor(keyMetadata({ project_id: null })));
    renderWithProviders(<ApplicationFormDialog open onOpenChange={() => {}} />);

    const select = await screen.findByLabelText("Project");
    fireEvent.change(select, { target: { value: "proj_2" } });
    fillNameAndSubmit();

    await waitFor(() => {
      const post = calls.find((c) => c.method === "POST");
      expect(post).toBeDefined();
      expect(post?.body).toMatchObject({ name: "Support Bot", project_id: "proj_2" });
    });
  });

  it("Test A - organization-level key + defaultProjectId: a contextual default is never an explicit selection", async () => {
    connectSession(RAW_ORG_KEY);
    const calls = mockApi(routesFor(keyMetadata({ project_id: null })));
    // Opened from proj_2's own detail page - this must not, by itself,
    // count as the user having chosen proj_2.
    renderWithProviders(
      <ApplicationFormDialog open onOpenChange={() => {}} defaultProjectId="proj_2" />,
    );

    const select = await screen.findByLabelText("Project");
    expect(select).toHaveValue("");

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Support Bot" } });
    const submit = screen.getByRole("button", { name: /create application/i });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(calls.find((c) => c.method === "POST")).toBeUndefined();

    // Now the user actually, explicitly selects proj_2.
    fireEvent.change(select, { target: { value: "proj_2" } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
        name: "Support Bot",
        project_id: "proj_2",
      });
    });
  });

  it("project-scoped key: scope is locked to the key's own project, no dropdown shown", async () => {
    connectSession(RAW_PROJECT_KEY);
    const calls = mockApi(
      routesFor(keyMetadata({ project_id: "proj_1", key_prefix: "afp_live_proj1" })),
    );
    renderWithProviders(<ApplicationFormDialog open onOpenChange={() => {}} />);

    await screen.findByDisplayValue("Web Frontend");
    expect(screen.queryByRole("combobox", { name: "Project" })).not.toBeInTheDocument();
    expect(screen.getByDisplayValue("Web Frontend")).toBeDisabled();

    fillNameAndSubmit();
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
        project_id: "proj_1",
      });
    });
  });

  it("Test C - project-scoped key: locked to its own project even with a stale defaultProjectId, and cannot be changed", async () => {
    connectSession(RAW_PROJECT_KEY);
    const calls = mockApi(
      routesFor(keyMetadata({ project_id: "proj_1", key_prefix: "afp_live_proj1" })),
    );
    // Opened from a *different* project's detail page - the connected
    // credential's own project must still win.
    renderWithProviders(
      <ApplicationFormDialog open onOpenChange={() => {}} defaultProjectId="proj_2" />,
    );

    const locked = await screen.findByDisplayValue("Web Frontend");
    // No selectable dropdown is offered at all - there is nothing for the
    // user to change, stale defaultProjectId or not.
    expect(screen.queryByRole("combobox", { name: "Project" })).not.toBeInTheDocument();
    expect(locked).toBeDisabled();

    fillNameAndSubmit();
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
        project_id: "proj_1",
      });
    });
  });

  it("unknown scope: no request can be submitted without an explicit project", async () => {
    connectSession(RAW_ORG_KEY);
    // Connected key cannot be matched to any metadata row -> scope unknown.
    const calls = mockApi(routesFor(keyMetadata({ key_prefix: "afp_live_unrel" })));
    renderWithProviders(<ApplicationFormDialog open onOpenChange={() => {}} />);

    await screen.findByText(/could not determine the connected key's scope/i);
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Support Bot" } });
    const submit = screen.getByRole("button", { name: /create application/i });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(calls.find((c) => c.method === "POST")).toBeUndefined();

    fireEvent.change(screen.getByLabelText("Project"), { target: { value: "proj_1" } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
        project_id: "proj_1",
      });
    });
  });

  it("Test B - unknown scope + defaultProjectId: a contextual default is never an explicit selection", async () => {
    connectSession(RAW_ORG_KEY);
    // Connected key cannot be matched to any metadata row -> scope unknown.
    const calls = mockApi(routesFor(keyMetadata({ key_prefix: "afp_live_unrel" })));
    renderWithProviders(
      <ApplicationFormDialog open onOpenChange={() => {}} defaultProjectId="proj_2" />,
    );

    await screen.findByText(/could not determine the connected key's scope/i);
    const select = screen.getByLabelText("Project");
    expect(select).toHaveValue("");

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Support Bot" } });
    const submit = screen.getByRole("button", { name: /create application/i });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(calls.find((c) => c.method === "POST")).toBeUndefined();

    // Now the user actually, explicitly selects proj_2.
    fireEvent.change(select, { target: { value: "proj_2" } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);
    await waitFor(() => {
      expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({
        project_id: "proj_2",
      });
    });
  });

  it("never renders the connected raw API key anywhere in the dialog", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(routesFor(keyMetadata({ project_id: null })));
    renderWithProviders(<ApplicationFormDialog open onOpenChange={() => {}} />);

    await screen.findByLabelText("Project");
    expect(document.body.innerHTML).not.toContain(RAW_ORG_KEY);
    expect(document.body.innerHTML).not.toContain("connected-secret-material");
  });

  it("does not render a project field at all when editing", async () => {
    connectSession(RAW_ORG_KEY);
    mockApi(routesFor(keyMetadata({ project_id: null })));
    const application: Application = {
      id: "app_1",
      project_id: "proj_1",
      name: "Existing app",
      slug: "existing-app",
      description: null,
      status: "active",
      environment: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };
    renderWithProviders(
      <ApplicationFormDialog open onOpenChange={() => {}} application={application} />,
    );

    await screen.findByDisplayValue("Existing app");
    expect(screen.queryByLabelText("Project")).not.toBeInTheDocument();
  });
});
