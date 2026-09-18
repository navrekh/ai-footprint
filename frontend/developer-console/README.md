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

Errors follow the backend contract `{"error": {code, message, request_id}}`,
with `X-Request-ID` on every response. The console maps 400/401/403/404/409/
422/429/5xx to developer-facing messages and displays the request ID.

## Resource-impact semantics

Estimated resource impact is always presented as a range with confidence,
coverage, methodology and provenance. The console never averages a
minimum/maximum into a single figure, never fabricates activity, and never
introduces scores, rankings, winners, or recommendations.

## Structure

```
src/
├── components/      shared UI and dialogs (components/ui = primitives)
├── layouts/         console shell
├── pages/           route-level screens
├── hooks/           session + TanStack Query hooks
├── types/           API contract types
└── lib/
    ├── api/         centralized client and resource calls
    ├── auth/        sessionStorage credential handling
    ├── errors/      error contract mapping
    └── utils/
```

Sprint scope: Dashboard, Projects, Project detail, Applications and API Keys
are implemented. Usage, Compare, Benchmarks, API Explorer and Documentation
are navigable placeholders.
