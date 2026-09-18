import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiExplorerPage } from "@/pages/ApiExplorerPage";
import { connectSession, mockApi, renderWithProviders } from "@/test/utils";

const RAW_KEY = "afp_live_orgcr-connected-secret-material";

const MINIMAL_SPEC = {
  paths: {
    "/v1/projects": {
      get: {
        summary: "List projects belonging to the authenticated organization",
        tags: ["projects"],
        parameters: [
          { name: "limit", in: "query", required: false, description: "Page size." },
          { name: "offset", in: "query", required: false, description: "Skip count." },
        ],
      },
    },
    "/v1/projects/{project_id}": {
      get: {
        summary: "Get a project",
        tags: ["projects"],
        parameters: [{ name: "project_id", in: "path", required: true, description: "Project id." }],
      },
    },
    "/v1/organizations": {
      post: {
        summary: "Sign up",
        tags: ["organizations"],
        requestBody: {
          content: {
            "application/json": { schema: { $ref: "#/components/schemas/OrganizationCreate" } },
          },
        },
      },
    },
  },
  components: {
    schemas: {
      OrganizationCreate: { example: { name: "Acme Corp" } },
    },
  },
};

function routes() {
  return [{ path: "/openapi.json", body: MINIMAL_SPEC }];
}

describe("ApiExplorerPage", () => {
  it("lists endpoints derived from the live OpenAPI document, grouped by tag", async () => {
    connectSession(RAW_KEY);
    mockApi(routes());
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    expect(select).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "GET /v1/projects" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "POST /v1/organizations" })).toBeInTheDocument();
  });

  it("executes a request through the existing authenticated client and renders the response, status and request ID", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi([
      ...routes(),
      {
        path: "/v1/projects",
        body: { items: [{ id: "proj_1", name: "Production" }], total: 1 },
      },
    ]);
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    fireEvent.change(select, { target: { value: "GET /v1/projects" } });
    fireEvent.click(screen.getByRole("button", { name: /execute/i }));

    await screen.findByText("200");
    expect(screen.getByText(/req_test/)).toBeInTheDocument();
    expect(screen.getByText(/"Production"/)).toBeInTheDocument();

    const apiCall = calls.find((c) => c.url.includes("/v1/projects") && !c.url.includes("openapi"));
    expect(apiCall?.authorization).toBe(`Bearer ${RAW_KEY}`);
  });

  it("substitutes path parameters into the request URL", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi([
      ...routes(),
      { path: "/v1/projects/proj_42", body: { id: "proj_42", name: "Production" } },
    ]);
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    fireEvent.change(select, { target: { value: "GET /v1/projects/{project_id}" } });
    fireEvent.change(await screen.findByLabelText("project_id (path)"), {
      target: { value: "proj_42" },
    });
    fireEvent.click(screen.getByRole("button", { name: /execute/i }));

    await waitFor(() => {
      expect(calls.some((c) => c.url.includes("/v1/projects/proj_42"))).toBe(true);
    });
  });

  it("pre-fills the request body from the backend's own OpenAPI example", async () => {
    connectSession(RAW_KEY);
    mockApi(routes());
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    fireEvent.change(select, { target: { value: "POST /v1/organizations" } });

    const body = (await screen.findByLabelText("Request body (JSON)")) as HTMLTextAreaElement;
    expect(body.value).toContain("Acme Corp");
  });

  it("shows the API error, code, and request ID on a failed request", async () => {
    connectSession(RAW_KEY);
    mockApi([
      ...routes(),
      {
        path: "/v1/projects",
        status: 401,
        body: { error: { code: "UNAUTHORIZED", message: "Invalid key.", request_id: "req_err" } },
      },
    ]);
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    fireEvent.change(select, { target: { value: "GET /v1/projects" } });
    fireEvent.click(screen.getByRole("button", { name: /execute/i }));

    await screen.findByText(/Your API key is invalid or expired/);
    expect(screen.getByText(/req_err/)).toBeInTheDocument();
  });

  it("never renders the connected raw API key anywhere in the explorer", async () => {
    connectSession(RAW_KEY);
    mockApi([
      ...routes(),
      { path: "/v1/projects", body: { items: [], total: 0 } },
    ]);
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    fireEvent.change(select, { target: { value: "GET /v1/projects" } });
    fireEvent.click(screen.getByRole("button", { name: /execute/i }));
    await screen.findByText("200");

    expect(document.body.innerHTML).not.toContain(RAW_KEY);
    expect(screen.getByText("Authorization: Bearer ••••••••")).toBeInTheDocument();
  });

  it("never places the API key in a request URL", async () => {
    connectSession(RAW_KEY);
    const calls = mockApi([...routes(), { path: "/v1/projects", body: { items: [], total: 0 } }]);
    renderWithProviders(<ApiExplorerPage />);

    const select = await screen.findByLabelText("Endpoint");
    fireEvent.change(select, { target: { value: "GET /v1/projects" } });
    fireEvent.click(screen.getByRole("button", { name: /execute/i }));
    await screen.findByText("200");

    for (const call of calls) {
      expect(call.url).not.toContain(RAW_KEY);
    }
  });
});
