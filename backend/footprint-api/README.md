# AI Footprint - Backend

AI Footprint estimates the resource impact (energy, water, CO2e) of AI
workloads - conversational, image, video, audio, coding and agentic - as
**ranges with confidence, evidence level and methodology version**, never
as a fabricated exact measurement. See `docs/PRD.md`, `docs/FRD.md`,
`docs/ARCHITECTURE.md` and `docs/METHODOLOGY.md` for the full product
specification this backend implements.

- **Sprint 1** delivered the backend foundation: FastAPI app, PostgreSQL
  persistence, the provider/model/methodology registries, the estimation
  engine, project-scoped API-key authentication and the initial
  stateless `/v1/estimate` / `/v1/batch-estimate` / `/v1/events` API.
- **Sprint 2** (this revision) turns that into a persistent, multi-tenant
  platform: organization/project management, a full API-key lifecycle
  (organization-level and project-scoped keys, expiry, revocation),
  durable workload/estimate persistence with provenance, idempotent event
  ingestion, and paginated workload/estimate history APIs.

No frontend, mobile app or browser extension is in scope for either
sprint.

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
  contract, slug generation, cursor pagination.
- `app/db/` - async engine/session and the shared declarative base.
- `app/models/` - SQLAlchemy persistence models.
- `app/schemas/` - Pydantic request/response contracts.
- `app/services/` - business services (auth, organizations, projects,
  API keys, workloads, estimates, batch, tenant-context resolution).
- `app/methodology/` - the estimation engine: validator, resolvers,
  per-metric estimators, uncertainty aggregation, confidence, and the
  pipeline that sequences them. Independent of the persistence layer -
  it takes a workload-shaped input and returns an `EstimateResult`; it
  has no knowledge of organizations, projects or HTTP.
- `app/providers/` - the provider adapter abstraction (structural in
  this sprint; adapters do not call any provider API yet).

### Multi-tenancy model

```text
Organization (tenant boundary)
   |
   +-- Project(s)
         |
         +-- API Key(s) - project-scoped
         +-- AIWorkload(s) -> Estimate
   +-- API Key(s) - organization-level
```

An API key belongs to exactly one **organization** and, optionally, to
one **project** within it:

- A **project-scoped key** (the Sprint 1 model) authenticates requests
  against that one project - it can submit events, and its reads
  (workload/estimate history) are hard-limited to that project.
- An **organization-level key** (`project_id` is `NULL`) exists to
  bootstrap and manage an organization's projects and keys before any
  project-scoped key exists for a given project, and to read across all
  of an organization's projects. It must supply an explicit `project_id`
  on write endpoints (`POST /v1/events`).

Every organization-scoped query is filtered by `organization_id` derived
from the authenticated API key - never from a client-supplied
`organization_id`/`project_id` in the request body alone. Cross-tenant
lookups return `404 NOT_FOUND` rather than `403 FORBIDDEN`, so a caller
can never distinguish "belongs to another organization" from "does not
exist."

### Architecture notes / design decisions

**Stateless `/v1/estimate` and `/v1/batch-estimate` vs. persisted
`/v1/events` (Sprint 1, preserved in Sprint 2).** The FRD lists
`Estimate.workload_id` as required, but `/v1/estimate` and
`/v1/batch-estimate` are specified as *calculate* endpoints while only
`/v1/events` is specified as *persist*. Resolved by keeping
`/v1/estimate` and `/v1/batch-estimate` fully stateless (no DB writes,
ephemeral generated IDs); `/v1/events` is the only endpoint that
persists `AIWorkload` + `Estimate`. Sprint 2 did not change this - it was
an explicit instruction not to silently turn the calculate-only endpoint
into a persistence one.

**Organization creation is the one unauthenticated endpoint.**
`POST /v1/organizations` has no prior auth context to bind to (it is the
signup step), so it bootstraps a default project and the organization's
first API key in the same transaction and returns the raw key once. This
is the only way to get started; there is no username/password/session
system, matching the PRD's API-key-centric developer flow without adding
an out-of-scope auth mechanism (OAuth, SSO).

**No RBAC beyond the organization tenant boundary.** Any valid,
non-revoked, non-expired API key belonging to organization X (whether
organization-level or project-scoped) can manage organization X's
projects and API keys. The only place a key's own project scope matters
is which project a write targets (`POST /v1/events`) and which
project(s) a read can see. This is deliberately not a permissions/roles
system - the sprint brief explicitly excludes "RBAC beyond the minimum
tenant authorization needed."

**Estimate provenance is denormalized.** `Estimate.provider` / `.model` /
`.model_version` are copied from the resolved registry entries at
calculation time, rather than requiring a join through `workload_id`, so
a persisted estimate is self-contained and independent of any future
change to how `AIWorkload` stores these fields (historical immutability).
Deeper snapshotting (embedding the exact `MethodologyFactor` row used) was
considered and deliberately not implemented - `methodology_version` +
`provider` + `model` + `activity_type` are sufficient to look up the
applicable factor set, since methodology factors are themselves
versioned and immutable (never overwritten, only superseded with a new
`effective_from`). Full factor-value snapshotting is left for a future
sprint if reproducibility requirements tighten further.

**Idempotency is a simple, project-scoped key match.** `EventCreateRequest.idempotency_key`
is optional; when supplied, `(project_id, idempotency_key)` is unique
(a database constraint, not just an application check). Resubmitting the
same key returns the original `workload_id`/`estimate_id` with
`idempotent_replay: true` - no request-body comparison, no queue, no
distributed locking, matching "a simple deterministic idempotency
mechanism," not an event-processing platform.

**`EventCreateResponse` is additive, not breaking.** Sprint 1 returned
`{"event_id", "estimate_id"}`. Sprint 2 adds `workload_id` (identical to
`event_id`, kept for compatibility), `status`
(`"measured" | "partial" | "insufficient_data"`, derived from the three
per-metric statuses, never stored) and `idempotent_replay`. Existing
clients reading only `event_id`/`estimate_id` are unaffected.

**Pagination is cursor-based, never offset.** `GET /v1/workloads` orders
by `created_at DESC, id DESC` (a stable order even when timestamps tie)
and pages via an opaque base64 cursor encoding the last row's
`(created_at, id)` - correct even as new workloads are inserted between
page fetches, unlike offset pagination. `GET /v1/projects` and
`GET /v1/api-keys` use simple limit/offset instead, since those lists are
low-cardinality, admin-style listings rather than growing event streams.

## Database

PostgreSQL via SQLAlchemy 2.x (async, `asyncpg` driver) and Alembic
migrations (sync, `psycopg` driver, derived from the same `DATABASE_URL`).
`Base.metadata.create_all()` is never used as a schema-management
mechanism - all schema changes go through Alembic revisions.

Tables: `organizations`, `projects`, `api_keys`, `providers`, `models`,
`methodologies`, `methodology_factors`, `ai_workloads`, `estimates`.

Sprint 2 migration (`ea0ba84cd47c_sprint_2_persistence_lifecycle`) adds:

- `organizations`: `slug` (unique), `status`
- `projects`: `slug` (unique per organization), `description`, `status`
- `api_keys`: `organization_id` (required FK), `expires_at`; `project_id`
  becomes nullable
- `ai_workloads`: `model_version`, `input_characters`, `output_characters`,
  `duration_ms`, `idempotency_key` (unique per project); indexes on
  `provider`, `model`, `activity_type`, `created_at`, and a composite
  `(project_id, created_at)` for the history query's ordering
- `estimates`: `provider`, `model`, `model_version` (denormalized
  provenance); index on `created_at`

Pre-existing rows are backfilled during the migration (organization/
project `slug` defaults to `id`; `api_keys.organization_id` is backfilled
from the linked project) rather than requiring an empty database.

`methodology_factors.provider` / `.model` remain plain nullable strings,
not foreign keys - the data contract (`data/methodology/README.md`)
explicitly allows generic factors with no provider/model.

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
  factor set, purely so a developer can exercise `/v1/estimate` locally
  end-to-end. It must never be run against a shared, staging or
  production database.

Adding a real, sourced methodology factor is a reviewed data-entry
process (see `data/methodology/README.md`), not a code change.

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
> point where `NULL` became meaningful, not a bug.

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
| POST | `/v1/api-keys` | any key | omit `project_id` for an org-level key |
| GET | `/v1/api-keys` | any key | limit/offset paginated; never returns the raw key/hash |
| POST | `/v1/api-keys/{id}/revoke` | any key | |
| POST | `/v1/estimate` | any key | stateless, not persisted |
| POST | `/v1/events` | any key | persists `AIWorkload` + `Estimate`; supports `idempotency_key` |
| POST | `/v1/batch-estimate` | any key | stateless, not persisted |
| GET | `/v1/workloads` | any key | cursor-paginated history, filterable |
| GET | `/v1/workloads/{id}` | any key | |
| GET | `/v1/estimates/{id}` | any key | |
| GET | `/v1/providers` | none | |
| GET | `/v1/models` | none | |
| GET | `/v1/methodology` | none | |

## Methodology principles

- Estimates are always **ranges** (`min`/`max`), never a single fabricated
  number, with `confidence`, `evidence_level`, `methodology_version` and
  `assumptions`.
- When no approved factor exists for a workload, the API returns an
  explicit `insufficient_data` status per metric rather than inventing a
  value; `partial` communicates "some but not all metrics measured"
  without ever letting a partial result look complete.
- Methodology versions are immutable once published; historical estimates
  keep the methodology version - and now also the provider/model/model
  version - used at calculation time (`Estimate` denormalizes these).
- Aggregation (batches, future coding-agent sessions) sums minimums and
  sums maximums independently - it never averages a range into false
  precision.

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
- No web frontend, mobile app or browser extension.
- No rate limiting implementation yet (error code and abstraction point
  exist; no limiter is wired up - explicitly out of scope for Sprint 2).
- No coding-agent session aggregation endpoint yet (the
  `parent_workload_id` relationship and `UncertaintyEngine.aggregate()`
  primitive are in place for a future sprint).
- No full methodology-factor snapshotting on `Estimate` - provenance is
  provider/model/model_version/methodology_version, not a copy of the
  exact factor row (see "Architecture notes" for why this is sufficient
  for Sprint 2).
- Idempotency is a simple key-match replay, not a request-body-hash
  comparison - resubmitting the same `idempotency_key` with a
  *different* payload silently returns the original result rather than
  erroring, matching "a simple deterministic idempotency mechanism" and
  not a general-purpose request-fingerprinting system.
- No RBAC beyond the organization tenant boundary (any valid key in an
  organization can manage that organization's projects/keys) - explicitly
  out of scope per the sprint brief.
- Docker Compose stack was authored and reviewed but could not be built
  in this sandbox (Docker Desktop was incompatible with the host macOS
  version); verify on a compatible machine or in CI before depending on it.
