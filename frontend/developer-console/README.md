# AI Footprint — Developer Console

Frontend for the existing AI Footprint REST API (`backend/footprint-api`).
The backend is authoritative: this console only consumes the documented
contract and never reimplements estimation, methodology, or resource-impact
logic in the browser.

## Stack

React 19 · TypeScript (strict) · Vite · Tailwind CSS v4 · Radix primitives ·
React Router · TanStack Query · Lucide icons.

## Setup

```bash
cd frontend/developer-console
npm install
cp .env.example .env     # set VITE_API_BASE_URL
npm run dev
```

| Script              | Purpose                        |
| ------------------- | ------------------------------ |
| `npm run dev`       | Local dev server               |
| `npm run build`     | Type-check and production build|
| `npm run typecheck` | TypeScript only                |
| `npm run lint`      | ESLint                         |
| `npm test`          | Vitest (unit/component tests)  |

`VITE_API_BASE_URL` is the API origin without the `/v1` suffix and without a
trailing slash (for example `https://api.example.com`). The production URL is
never hardcoded. The API must list the console origin in its CORS
`ALLOWED_ORIGINS` (ADR-012); the console sends no cookies.

## Authentication (ADR-012)

* The developer enters an API key in the Connect screen through a masked input.
* The key is verified against a real authenticated endpoint
  (`GET /v1/projects?limit=1`) before any session is recorded — authentication
  is never assumed to succeed.
* The key is stored in `sessionStorage` only: never `localStorage`, never
  cookies, never a URL, query parameter, route, log line, or analytics payload.
* `Disconnect` clears the key and the cached query data.
* A `401` from any request clears the session and returns to Connect.
* `sessionStorage` is not an XSS defence — the console renders no
  `dangerouslySetInnerHTML` and never injects API responses as HTML.

## API surface consumed

All requests carry `Authorization: Bearer <API_KEY>`.

| Resource      | Calls                                                                                                          |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| Organizations | `GET /v1/organizations/{organization_id}`                                                                       |
| Projects      | `GET /v1/projects`, `POST /v1/projects`, `GET /v1/projects/{project_id}`, `PATCH /v1/projects/{project_id}`      |
| Applications  | `GET /v1/applications`, `POST /v1/applications`, `GET /v1/applications/{application_id}`, `PATCH /v1/applications/{application_id}` |
| API keys      | `GET /v1/api-keys`, `POST /v1/api-keys`, `POST /v1/api-keys/{api_key_id}/revoke`                                |
| Usage         | `GET /v1/usage/summary`, `/by-provider`, `/by-model`, `/by-activity`, `/by-application`, `/timeseries`          |
| Compare       | `POST /v1/compare`                                                                                               |
| Benchmarks    | `GET /v1/benchmarks`, `GET /v1/benchmarks/{benchmark_id}`, `POST /v1/benchmarks/run`                            |
| API Explorer  | `GET /openapi.json` (endpoint list) plus whichever endpoint the developer selects, all through the same client  |

`GET /v1/methodology` is not called by the console: it is a separate
registry endpoint, and no Usage/Compare/Benchmark response embeds a
reference to it in a way the console can safely join without showing
information that isn't actually part of that response. See "Resource-
impact semantics" below.

Errors follow the backend contract `{"error": {code, message, request_id}}`,
with `X-Request-ID` on every response. The console maps 400/401/403/404/409/
422/429/5xx to developer-facing messages and displays the request ID.

## Connected credential scope (known API limitation)

The API has no endpoint that returns the authenticated key's own identity
(no `/v1/me` or equivalent), and the backend is not changed to add one. The
console identifies the connected key by matching the session-held raw key
against the non-secret `key_prefix` metadata `GET /v1/api-keys` returns for
every key in the organization (`src/lib/auth/connectedKey.ts`). The backend
defines `key_prefix` as a literal leading slice of the raw key
(`app/core/security.py`), so this match is exact, not a heuristic — and if
it is ever ambiguous (more than one row matches) or missing, the console
treats the scope as **unknown** rather than guessing.

This identified scope drives two places in the UI:

* **Creating an API key** (`ApiKeysPage.tsx`): an organization-level
  credential can choose organization-level or an explicit project for the
  new key; a project-scoped credential is locked to its own project, with
  no organization-level option and no other project selectable; an
  unidentifiable ("unknown") credential must also choose an explicit
  project and is never offered an organization-level option either, since
  the console cannot verify that choice is safe.
* **Creating an application** (`ApplicationFormDialog.tsx`): applications
  always belong to exactly one project, so there is no "organization-level"
  choice here at all. A project-scoped credential is locked to its own
  project; an organization-level or unknown credential must always choose
  an explicit project from the full list — the console never offers a
  "use the key's own project" default, which would be unverifiable (an
  organization-level key has no project of its own) or unverified (a
  project-scoped key's identity might not have matched).

In every case, the value actually submitted to the API is the identified
credential's own project id when locked, or the explicit selection
otherwise — never inferred, and never overridden by stale form state (e.g.
a `defaultProjectId` pre-filled from a different project's detail page).

**Dashboard organization identity** (`DashboardPage.tsx`) is resolved the
same way: `GET /v1/api-keys` exposes `organization_id` as non-secret
metadata on the connected key's row, so an organization with zero projects
still shows its details. The first project's `organization_id` remains a
documented fallback for the rarer case where the connected key cannot be
identified (e.g. more than 200 keys in the organization, past this
console's list page size) — real, organization-scoped data, never a
fabricated id. If neither source resolves, the dashboard says so rather
than rendering nothing or misleading text.

## Resource-impact semantics

Estimated resource impact is always presented as a range. The console
never averages a minimum/maximum into a single figure, never fabricates
activity, and never introduces scores, rankings, winners, or
recommendations. `insufficient_data` renders as literal text, never as `0`
or `N/A`; a `partial` aggregate always shows its
`measured_workloads`/`total_workloads` completeness alongside the range,
never silently implying full coverage. This applies uniformly across
Usage, Compare, and Benchmarks (the latter two share one result-rendering
component, `ComparisonResultCard`, specifically so this guarantee cannot
diverge between them).

**What's rendered is scoped exactly to what each response actually
contains — nothing is inferred or joined in from elsewhere:**

* **Usage** (`GET /v1/usage/*`) returns `status`/`min`/`max`/`unit` plus
  workload-count completeness. It does not return `confidence` or
  `methodology_version`, so the Usage UI does not display them.
* **Compare / Benchmark run** (`POST /v1/compare`,
  `POST /v1/benchmarks/run`) return, per candidate, ranges plus
  `confidence`, `evidence_level`, `accounting_boundary`,
  `methodology_version`, and `assumptions`. They do not return
  `limitations` or source/provenance text — that only exists in the
  separate `GET /v1/methodology` registry, keyed by version. The console
  does not join that registry in here, because doing so would show
  information that isn't actually part of the compare/benchmark
  response; the expandable "Methodology & provenance" panel says so
  explicitly rather than silently omitting the section.
* **Benchmark definitions** (`GET /v1/benchmarks`,
  `GET /v1/benchmarks/{id}`) return only `benchmark_id`, `version`,
  `name`, `description`, `activity_type`, `modality`, and `parameters` —
  no status/availability, normalization basis, methodology version,
  assumptions, limitations, or provenance. The benchmark detail page
  renders exactly those seven fields and says explicitly that richer
  methodology/provenance detail isn't available until you run the
  benchmark (at which point it comes from the run response, per
  candidate, as above).

## API Explorer design note

The explorer does not embed the backend's Swagger UI (`GET /docs`),
because Swagger UI persists whatever bearer token a user enters into its
own `localStorage` by default — a direct ADR-012 violation (sessionStorage
only). Instead it fetches the backend's own generated `GET /openapi.json`
to enumerate endpoints, parameters, and request-body examples (so the
endpoint list is never hand-duplicated and can never drift from the real
contract), and executes every request through the same `apiRequest`
client every other page uses — same Authorization-header injection, same
`credentials: "omit"`, same 401-clears-session handling. The connected
raw key is never rendered; the explorer only ever displays
`Authorization: Bearer ••••••••`.

## Structure

```
src/
├── components/      shared UI and dialogs (components/ui = primitives,
│                      components/resource = range/estimate/candidate
│                      display shared by Usage, Compare and Benchmarks)
├── layouts/         console shell
├── pages/           route-level screens
├── hooks/           session + TanStack Query hooks
├── types/           API contract types
└── lib/
    ├── api/         centralized client, resource calls, OpenAPI helper
    ├── auth/        sessionStorage credential handling
    ├── errors/      error contract mapping
    └── utils/
```

Sprint scope: Dashboard, Projects, Project detail, Applications, API Keys,
Usage, Compare, Benchmarks (list, detail, run) and the API Explorer are
implemented (Sprint 5C + 5D). Documentation remains a navigable placeholder.
