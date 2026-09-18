# AI Footprint - Backend

AI Footprint estimates the resource impact (energy, water, CO2e) of AI
workloads - conversational, image, video, audio, coding and agentic - as
**ranges with confidence, evidence level and methodology version**, never
as a fabricated exact measurement. See `docs/PRD.md`, `docs/FRD.md`,
`docs/ARCHITECTURE.md` and `docs/METHODOLOGY.md` for the full product
specification this backend implements.

**New here?** [`docs/QUICKSTART.md`](../../docs/QUICKSTART.md) gets you
from zero to your first footprint estimate in about 10 minutes.

- **Sprint 1** delivered the backend foundation: FastAPI app, PostgreSQL
  persistence, the provider/model/methodology registries, the estimation
  engine, project-scoped API-key authentication and the initial
  stateless `/v1/estimate` / `/v1/batch-estimate` / `/v1/events` API.
- **Sprint 2** turned that into a persistent, multi-tenant platform:
  organization/project management, a full API-key lifecycle
  (organization-level and project-scoped keys, expiry, revocation),
  durable workload/estimate persistence with provenance, idempotent event
  ingestion, and paginated workload/estimate history APIs.
- **Sprint 3** added the developer platform and usage intelligence
  layer: an `Application` entity between Project and AIWorkload,
  application-aware event submission, and six usage intelligence
  endpoints (summary, and breakdowns by provider/model/activity/
  application, plus a time series) - all derived from persisted data via
  PostgreSQL aggregation, with no separate usage ledger.
- **Sprint 4** added AI Resource Intelligence: `POST /v1/compare`
  (evaluate one workload across multiple provider/model candidates,
  each independently, never ranked), standardized/versioned benchmark
  definitions (`GET /v1/benchmarks`, `GET /v1/benchmarks/{id}`,
  `POST /v1/benchmarks/run`), normalized resource intensity (per
  token/image/second/minute where defensible), and a read-only
  methodology-data governance validator (`scripts/validate_methodology.py`).
- **Sprint 5A** (this revision) is developer-experience productization
  over the existing API: complete OpenAPI documentation (descriptions,
  examples, and documented error responses for every endpoint), CORS
  for the future Developer Console (per `docs/ADR-012-console-authentication.md`),
  and this refreshed README/Quick Start. **No new endpoint, schema,
  estimation logic, or methodology data was introduced.**

No frontend, Python SDK, or browser extension exists in this repository
yet - see `docs/FRD.md` section 36 for the Sprint 5B/5C target
architecture (a thin REST-client SDK and a static developer console),
neither of which is implemented by Sprint 5A.

## Architecture

```text
Client
  -> API layer (FastAPI, app/api/)
  -> Authentication (Authorization: Bearer <API_KEY> -> Organization -> optional Project)
  -> Services (app/services/) - thin orchestration, no calculation logic
  -> Estimation pipeline (app/methodology/) -
       Validate -> Resolve Provider -> Resolve Model -> Resolve Methodology
       -> Resolve Factors -> Energy/Water/Carbon Estimate
       -> Uncertainty Propagation -> Confidence -> EstimateResult
  -> Persistence (PostgreSQL via SQLAlchemy 2.x async + Alembic migrations)
```

Module boundaries follow `docs/ARCHITECTURE.md` section 5:

- `app/api/` - HTTP routes and dependency wiring only (thin controllers).
- `app/core/` - configuration, security, structured logging, error
  contract, slug generation, cursor pagination, shared DB-error
  classification.
- `app/db/` - async engine/session and the shared declarative base.
- `app/models/` - SQLAlchemy persistence models.
- `app/schemas/` - Pydantic request/response contracts.
- `app/services/` - business services (auth, organizations, projects,
  applications, API keys, workloads, estimates, batch, usage
  intelligence, tenant-context resolution).
- `app/methodology/` - the estimation engine: validator, resolvers,
  per-metric estimators, uncertainty aggregation, confidence, and the
  pipeline that sequences them. Independent of the persistence layer and
  of the usage/application layer - it takes a workload-shaped input and
  returns an `EstimateResult`; it has no knowledge of organizations,
  projects, applications or HTTP.
- `app/providers/` - the provider adapter abstraction (structural in
  this sprint; adapters do not call any provider API yet).

### Domain hierarchy

```text
Organization (tenant boundary)
   |
   +-- Project (operational boundary, API-key scope, usage aggregation)
         |
         +-- Application (a named AI product/service/environment)
         |     |
         |     +-- AIWorkload(s) -> Estimate
         |
         +-- API Key(s) - project-scoped
         +-- AIWorkload(s) without an application -> Estimate
   +-- API Key(s) - organization-level
```

An API key belongs to exactly one **organization** and, optionally, to
one **project** within it (unchanged from Sprint 2 - Sprint 3 does not
introduce application-scoped keys, per the PRD/FRD's explicit deferral):

- A **project-scoped key** authenticates requests against that one
  project - it can submit events, manage that project's applications,
  and its reads (workload/estimate/application/usage) are hard-limited
  to that project.
- An **organization-level key** (`project_id` is `NULL`) bootstraps and
  manages projects/applications/keys before any project-scoped key
  exists, and reads/aggregates across all of an organization's projects.
  It must supply an explicit `project_id` on write endpoints.

An `Application` belongs to exactly one project. A workload may
optionally reference an application, but only one that belongs to the
same project the workload is being persisted under - validated on every
submission, never inferred or fabricated.

Every organization-scoped query is filtered by `organization_id` derived
from the authenticated API key - never from a client-supplied value.
Cross-tenant lookups return `404 NOT_FOUND` rather than `403 FORBIDDEN`,
so a caller can never distinguish "belongs to another organization" from
"does not exist." Single-record reads (workload/estimate/application by
id) enforce the same project-scope rule as their collection endpoints.

### Architecture notes / design decisions

**Stateless `/v1/estimate` and `/v1/batch-estimate` (Sprint 1, preserved
through every later sprint).** These remain calculate-only with no DB
writes; only `/v1/events` persists `AIWorkload` + `Estimate`. Sprint 3
did not touch either stateless endpoint.

**Organization creation is the one unauthenticated endpoint** (Sprint
2). `POST /v1/organizations` bootstraps a default project and first API
key in the same transaction.

**No RBAC beyond the organization tenant boundary** (Sprint 2, still
true in Sprint 3). Any valid key in organization X can manage X's
projects, applications and keys. A key's own project scope only matters
for which project a write targets and which project(s)/application(s) a
read can see.

**Application/project mismatch has its own error code, distinct from
"does not exist."** `APPLICATION_NOT_FOUND` is opaque (the application
does not exist anywhere the caller's organization can see);
`APPLICATION_PROJECT_MISMATCH` means the application exists in the
caller's own organization but a different project - a legitimate,
specific validation error rather than a tenant leak, since the caller's
organization already has visibility into it. This mirrors the existing
`ForbiddenError` precedent for a project-scoped key's own project
mismatch in `tenant_context.resolve_target_project_id`.

**`application_id` is nullable and never backfilled or required.**
Existing Sprint 1/2 workloads have no application and remain fully
valid; new workloads may omit it too. There is no migration path that
assigns historical workloads to a fabricated application.

**Usage intelligence has no ledger.** `GET /v1/usage/*` compute
everything from `ai_workloads` JOIN `estimates` at query time via
PostgreSQL aggregate functions with `FILTER (WHERE ...)` clauses - the
same additive min/max-sum, per-metric-independent math as
`UncertaintyEngine.aggregate()` and `BatchService`, just pushed down to
the database instead of run over an in-memory list. The
ok/partial/insufficient_data decision itself
(`determine_metric_status`) was extracted out of `UncertaintyEngine` so
both call sites share the exact same rule rather than reimplementing it.
No new table, materialized view, Redis or warehouse was introduced.

**`by-application` excludes unassigned workloads** rather than grouping
them into a synthetic "none" bucket - a deliberate, minimal scope choice
consistent with the sprint's explicit exclusion of application-scoped
billing/analytics features.

**Usage date ranges default to the last 30 days when omitted**, and time
series requests are rejected with `INVALID_DATE_RANGE` if the requested
range/granularity combination would produce more than 400 buckets -
bounding an otherwise-unbounded query without needing a warehouse or
pagination on the time series endpoint itself.

**A project-scoped key's `project`/`application` usage filters are
hard-scoped, not rejected.** Reusing the same
`resolve_optional_project_filter` helper the workload-history list
endpoint already used in Sprint 2: a project-scoped key's usage queries
always run against its own project regardless of what filter value it
supplies, and an organization-level key's filter is constrained by the
mandatory `organization_id` condition either way - so a foreign
project/application id can never leak data, whether or not it is
explicitly rejected. `GET /v1/usage/*` follows the same convention as
`GET /v1/workloads` rather than inventing stricter validation
inconsistent with the rest of the API.

## Database

PostgreSQL via SQLAlchemy 2.x (async, `asyncpg` driver) and Alembic
migrations (sync, `psycopg` driver, derived from the same `DATABASE_URL`).
`Base.metadata.create_all()` is never used as a schema-management
mechanism - all schema changes go through Alembic revisions.

Tables: `organizations`, `projects`, `applications`, `api_keys`,
`providers`, `models`, `methodologies`, `methodology_factors`,
`ai_workloads`, `estimates`.

Sprint 3 migration (`9fdd13a3da4f_sprint_3_application_and_usage`) adds:

- `applications`: `id`, `project_id` (FK, cascade delete), `name`,
  `slug` (unique per project via `uq_application_project_slug`),
  `description`, `status`, `environment`, timestamps.
- `ai_workloads.application_id`: nullable FK to `applications.id`
  (`ON DELETE SET NULL` - deactivating or, hypothetically, removing an
  application never deletes historical workloads/estimates), indexed
  for the `by-application` usage query.

No backfill was needed (the new table starts empty; the new column is
nullable from the start), unlike Sprint 2's migration which had to
backfill pre-existing rows.

`methodology_factors.provider` / `.model` remain plain nullable strings,
not foreign keys - the data contract (`data/methodology/README.md`)
explicitly allows generic factors with no provider/model.

### Indexes for usage queries

Usage aggregation relies on indexes already added in Sprint 2
(`ai_workloads.organization_id`, `.project_id`, `.provider`, `.model`,
`.activity_type`, `.created_at`, and the composite
`(project_id, created_at)`), plus Sprint 3's new
`ai_workloads.application_id` index. No additional indexes were found to
be necessary for Sprint 3's query patterns; `EXPLAIN` was not required
since every usage query filters on already-indexed columns and
aggregates via `FILTER (WHERE ...)` rather than post-processing in
Python.

## No fabricated environmental factors

Per `docs/METHODOLOGY.md` and `data/methodology/README.md`, this codebase
contains **zero** invented environmental coefficients. The
`methodology_factors` table ships empty in a fresh migration. The only
factor values that exist anywhere in this repository are:

- Values created directly inside `tests/factories.py` / test files, whose
  `source` field is always literally prefixed `TEST_ONLY -` and which use
  `evidence_level=6` / `confidence=low`, and
- An **opt-in** `--with-test-only-demo-data` flag on `scripts/seed.py`
  that seeds an equally clearly labeled `TEST_ONLY-0.1` methodology/model/
  factor set, purely so a developer can exercise `/v1/estimate` and the
  usage endpoints locally end-to-end. It must never be run against a
  shared, staging or production database.

Adding a real, sourced methodology factor is a reviewed data-entry
process (see `data/methodology/README.md`), not a code change. Usage
intelligence inherits this guarantee automatically: it only aggregates
factors already validated by the estimation pipeline, and workloads with
no defensible factor are reported as `insufficient_data`, never as zero.

## Local setup

Requirements: Python 3.13+, and either Docker + Docker Compose, or a
local PostgreSQL 16 instance.

```bash
cd backend/footprint-api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # adjust DATABASE_URL if not using Docker Compose
```

### Environment variables

See `.env.example`. Required: `DATABASE_URL`, `ENVIRONMENT`, `LOG_LEVEL`,
`API_KEY_PREFIX`. No secrets are committed; `.env` is git-ignored.

### Docker

```bash
docker compose up --build
```

This starts PostgreSQL and the API (http://localhost:8000). Run
migrations and seed data once the stack is up:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed
```

> Note: this environment's Docker Desktop build is incompatible with the
> host's macOS version and could not be exercised here. The Dockerfile/
> Compose file follow the standard FastAPI + Postgres pattern and were
> reviewed but not built in this sandbox - please verify
> `docker compose up --build` in CI or on a compatible machine before
> relying on it.

### Without Docker (local PostgreSQL)

```bash
createdb footprint
alembic upgrade head
python -m scripts.seed                    # providers + a demo org/project/API key
# python -m scripts.seed --with-test-only-demo-data   # + a TEST_ONLY estimation demo
uvicorn app.main:app --reload
```

## Migrations

```bash
alembic upgrade head        # apply
alembic downgrade -1        # roll back one revision
alembic upgrade head        # re-apply
alembic check                # confirm no drift between models and migrations
alembic revision --autogenerate -m "description"   # create a new migration
```

> The Sprint 2 migration's `downgrade()` will fail if any
> organization-level (`project_id IS NULL`) API key exists, since
> `project_id` cannot be restored to `NOT NULL` while `NULL` rows are
> present - an inherent, intentional limitation of downgrading past the
> point where `NULL` became meaningful, not a bug. The Sprint 3 migration
> has no such constraint (its new column and table are both safe to add
> and remove regardless of existing data).

## Running tests

Tests run against a **real PostgreSQL database** (a dedicated
`footprint_test` database, created automatically if missing) - never
SQLite and never `create_all()`. Each test runs inside a transaction that
is rolled back afterward, so tests never leak state into each other.

```bash
export TEST_DATABASE_URL=postgresql+asyncpg://footprint:footprint@localhost:5432/footprint_test
pytest                    # unit + integration + security
pytest tests/unit
pytest tests/integration
pytest tests/security
ruff check app tests scripts
mypy app
```

## API documentation

Once running: `GET /docs` (Swagger UI) and `GET /openapi.json`.

### Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | none | liveness |
| POST | `/v1/organizations` | none | signup: creates org + default project + first API key |
| GET | `/v1/organizations/{id}` | any key | only the caller's own organization |
| POST | `/v1/projects` | any key | |
| GET | `/v1/projects` | any key | limit/offset paginated |
| GET | `/v1/projects/{id}` | any key | |
| PATCH | `/v1/projects/{id}` | any key | |
| POST | `/v1/applications` | any key | omit `project_id` for a project-scoped key |
| GET | `/v1/applications` | any key | filterable by `project`, limit/offset paginated |
| GET | `/v1/applications/{id}` | any key | |
| PATCH | `/v1/applications/{id}` | any key | status/environment/description/name only |
| POST | `/v1/api-keys` | any key | omit `project_id` for an org-level key |
| GET | `/v1/api-keys` | any key | limit/offset paginated; never returns the raw key/hash |
| POST | `/v1/api-keys/{id}/revoke` | any key | |
| POST | `/v1/estimate` | any key | stateless, not persisted |
| POST | `/v1/events` | any key | persists `AIWorkload` + `Estimate`; supports `idempotency_key`, optional `application_id` |
| POST | `/v1/batch-estimate` | any key | stateless, not persisted |
| GET | `/v1/workloads` | any key | cursor-paginated history, filterable |
| GET | `/v1/workloads/{id}` | any key | |
| GET | `/v1/estimates/{id}` | any key | |
| GET | `/v1/usage/summary` | any key | totals, coverage, energy/water/carbon ranges for a period |
| GET | `/v1/usage/by-provider` | any key | limit/offset paginated |
| GET | `/v1/usage/by-model` | any key | grouped by provider/model/model_version; limit/offset paginated |
| GET | `/v1/usage/by-activity` | any key | limit/offset paginated |
| GET | `/v1/usage/by-application` | any key | excludes unassigned workloads; limit/offset paginated |
| GET | `/v1/usage/timeseries` | any key | `granularity=day\|week\|month`; bounded to 400 buckets |
| POST | `/v1/compare` | any key | evaluate one workload across 2-`MAX_COMPARE_CANDIDATES` provider/model candidates; never ranked |
| GET | `/v1/benchmarks` | none | static, versioned benchmark definitions |
| GET | `/v1/benchmarks/{id}` | none | |
| POST | `/v1/benchmarks/run` | any key | executes a benchmark via the same mechanism as `/v1/compare` |
| GET | `/v1/providers` | none | |
| GET | `/v1/models` | none | |
| GET | `/v1/methodology` | none | |

All `/v1/usage/*` endpoints accept `from`, `to`, `project`, `application`,
`provider`, `model` and `activity_type` query filters (composable), and
default to the trailing 30 days when `from`/`to` are omitted.

Complete request/response schemas, examples and error responses for
every endpoint above are in the generated OpenAPI document (`/docs`,
`/openapi.json`) - the table above is a quick reference, not the source
of truth.

### Request correlation (request_id / workload_id / estimate_id)

Every response - success or error - carries an `X-Request-ID` response
header, generated fresh per request (`app/core/request_id.py`). Error
response bodies additionally embed the same value as `error.request_id`.
Success response bodies do not repeat it in the JSON body (check the
header), except where a resource id doubles as correlation - `workload_id`
and `estimate_id` from `POST /v1/events` let you look the record up later
via `GET /v1/workloads/{id}` / `GET /v1/estimates/{id}`. An `estimate_id`
returned by the *stateless* `POST /v1/estimate` has no persisted row
behind it - nothing to look up, by design.

When reporting an issue, include the `X-Request-ID` (or `error.request_id`)
value - it is what shows up in this service's structured logs.

### Idempotency

`POST /v1/events` accepts an optional `idempotency_key` (1-255
characters). Resubmitting the same key for the same project returns the
*original* `workload_id`/`estimate_id`/`status` with `idempotent_replay:
true`, rather than creating a duplicate measurement or erroring. This is
enforced by a database unique constraint on `(project_id,
idempotency_key)`, not just an application-level check, so it is safe
under concurrent retries (e.g. a network timeout followed by a client
retry) - the loser of a race is transparently turned into a replay of
the winner, never a 500 or a duplicate row. Idempotency keys are scoped
per project; the same key in a different project is a different key.
`/v1/estimate`, `/v1/batch-estimate`, `/v1/compare` and
`/v1/benchmarks/run` are stateless and have no idempotency
concept - nothing is persisted to replay.

### Errors

Every error response has the same shape:

```json
{
  "error": {
    "code": "MODEL_NOT_SUPPORTED",
    "message": "The requested model is not currently supported.",
    "request_id": "req_..."
  }
}
```

| Code | HTTP status | Meaning |
|---|---|---|
| `INVALID_REQUEST` | 400 | Malformed or oversized request (e.g. batch/candidate limit exceeded). |
| `MISSING_PARAMETER` | 400 | A required parameter was omitted (e.g. `project_id` for an org-level key). |
| `INVALID_DATE_RANGE` | 400 | `from` is after `to`, or the requested range/granularity exceeds bounds. |
| `UNAUTHORIZED` | 401 | No `Authorization` header. |
| `INVALID_API_KEY` | 401 | Unknown, malformed, or revoked key. |
| `API_KEY_EXPIRED` | 401 | Key existed and was valid, but its `expires_at` has passed. |
| `FORBIDDEN` | 403 | A project-scoped key targeted a different project explicitly. |
| `NOT_FOUND` | 404 | Generic resource-not-found (organization/project/application/workload/estimate/API key). Opaque: never distinguishes "doesn't exist" from "belongs to another tenant." |
| `PROVIDER_NOT_FOUND` | 404 | Unknown `provider`. |
| `MODEL_NOT_FOUND` | 404 | Unknown `model` for that provider (or that `model_version`). |
| `APPLICATION_NOT_FOUND` | 404 | Unknown application, or one outside the caller's organization. |
| `BENCHMARK_NOT_FOUND` | 404 | Unknown `benchmark_id`. |
| `MODEL_NOT_SUPPORTED` | 422 | Model is deprecated, or does not support the requested modality. |
| `INVALID_WORKLOAD` | 422 | e.g. an activity_type/modality mismatch, or a zero-quantity text workload. |
| `APPLICATION_PROJECT_MISMATCH` | 422 | The application exists in the caller's organization but a different project. |
| `METHODOLOGY_UNAVAILABLE` | 200 | Reserved; not currently raised as an HTTP error - see `insufficient_data` status instead. |
| `RATE_LIMITED` | 429 | Reserved for a future limiter; not currently enforced (see Known limitations). |
| `INTERNAL_ERROR` | 500 | Unhandled server error. Never leaks a stack trace. |

Note: a request that reaches Pydantic's own validation (a missing
required field, a wrong type, an out-of-range value) returns FastAPI's
standard `422` shape, which this API's global handler rewrites into the
same `{"error": {...}}` envelope with code `INVALID_REQUEST` or
`MISSING_PARAMETER`.

### CORS

`CORSMiddleware` is configured per `docs/ADR-012-console-authentication.md`:
an explicit, environment-driven origin allowlist (`ALLOWED_ORIGINS`,
comma-separated exact origins - never a wildcard), `allow_credentials`
is always `False` (authentication is the `Authorization` header, never a
cookie), and only `GET`/`POST`/`PATCH`/`OPTIONS` with
`Authorization`/`Content-Type` headers are permitted. CORS fails closed:
with `ALLOWED_ORIGINS` unset, no browser origin can call this API
cross-origin at all. This exists to support a future browser-based
Developer Console; it has no effect on server-to-server callers (SDKs,
`curl`, backend integrations), which are never subject to CORS.

## Methodology principles

- Estimates are always **ranges** (`min`/`max`), never a single fabricated
  number, with `confidence`, `evidence_level`, `methodology_version` and
  `assumptions`.
- When no approved factor exists for a workload, the API returns an
  explicit `insufficient_data` status per metric rather than inventing a
  value; `partial` communicates "some but not all metrics measured"
  without ever letting a partial result look complete - true whether
  aggregating a single event, a batch, or a usage query across
  thousands of workloads.
- Methodology versions are immutable once published; historical estimates
  keep the methodology version - and the provider/model/model version -
  used at calculation time (`Estimate` denormalizes these).
- Aggregation (batches, usage intelligence, future coding-agent sessions)
  sums minimums and sums maximums independently - it never averages a
  range into false precision, and measurement coverage
  (`measured`/`partial`/`insufficient_data` workload counts and
  `coverage_percent`) is always reported explicitly alongside the range.

See `docs/METHODOLOGY.md` for the full accounting-boundary, evidence-level
and confidence model.

## Security principles

- Raw API keys are never persisted - only a SHA-256 hash and a short,
  non-sensitive prefix for display/identification. The raw key is
  returned exactly once, at creation time (`POST /v1/organizations` or
  `POST /v1/api-keys`).
- All protected endpoints require `Authorization: Bearer <API_KEY>`,
  resolved through API key -> Organization -> optional Project. Expired
  keys are rejected with a distinct `API_KEY_EXPIRED` code; revoked/
  unknown keys with `INVALID_API_KEY`.
- Tenant isolation is enforced at the service layer using the
  organization_id derived from the authenticated key, never a
  client-supplied one: cross-tenant reads/writes return `404` (existence
  is never confirmed or denied differently for another tenant's data).
  Single-record reads (workload/estimate/application by id) enforce the
  same project scope as their collection endpoints.
- Application ownership is validated on every workload submission that
  references one: it must belong to the target project, with
  `APPLICATION_NOT_FOUND` (opaque) vs. `APPLICATION_PROJECT_MISMATCH`
  (explicit, same-organization) distinguishing the two failure modes.
- Errors follow a single consistent contract
  (`{"error": {"code", "message", "request_id"}}`) and never leak stack
  traces; every request gets a `request_id` (also returned as the
  `X-Request-ID` header) for log correlation.
- Structured JSON logs never contain API keys, secrets, prompts or
  generated content - verified by tests that inspect captured log
  records for the raw key value.
- No secrets are committed; configuration is environment-based
  (`.env`, git-ignored).

## Known limitations

- Methodology factors are not yet populated in the seed data (by design -
  see "No fabricated environmental factors" above).
- Provider adapters (`app/providers/`) are structural only; they do not
  call any provider API yet.
- No web frontend, mobile app, or browser extension.
- No rate limiting implementation yet (error code and abstraction point
  exist; no limiter is wired up - explicitly out of scope).
- No coding-agent session aggregation endpoint yet (the
  `parent_workload_id` relationship and `UncertaintyEngine.aggregate()`
  primitive are in place for a future sprint).
- No full methodology-factor snapshotting on `Estimate` - provenance is
  provider/model/model_version/methodology_version, not a copy of the
  exact factor row.
- Idempotency is a simple key-match replay, not a request-body-hash
  comparison.
- No RBAC beyond the organization tenant boundary, and no
  application-scoped API keys (both explicitly deferred by the PRD/FRD).
- `by-application` usage excludes workloads with no application rather
  than reporting an "unassigned" bucket.
- Usage breakdown endpoints use limit/offset pagination (consistent with
  `/v1/projects` and `/v1/api-keys`); `/v1/usage/timeseries` is instead
  bounded by a maximum bucket count (400) rather than paginated, since a
  time series is naturally ordered and callers control its size via
  `granularity` and date range.
- Docker Compose stack was authored and reviewed but could not be built
  in this sandbox (Docker Desktop was incompatible with the host macOS
  version); verify on a compatible machine or in CI before depending on it.
