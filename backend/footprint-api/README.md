# AI Footprint - Backend (Sprint 1: Backend Foundation)

AI Footprint estimates the resource impact (energy, water, CO2e) of AI
workloads - conversational, image, video, audio, coding and agentic - as
**ranges with confidence, evidence level and methodology version**, never
as a fabricated exact measurement. See `docs/PRD.md`, `docs/FRD.md`,
`docs/ARCHITECTURE.md` and `docs/METHODOLOGY.md` for the full product
specification this backend implements.

This sprint delivers the backend foundation only: FastAPI app, PostgreSQL
persistence, the provider/model/methodology registries, the estimation
engine, API-key authentication, multi-tenant isolation and the initial
REST API. No frontend, mobile app or browser extension is in scope.

## Architecture

```text
Client
  -> API layer (FastAPI, app/api/)
  -> Authentication (Authorization: Bearer <API_KEY> -> Project -> Organization)
  -> Services (app/services/) - thin orchestration, no calculation logic
  -> Estimation pipeline (app/methodology/) -
       Validate -> Resolve Provider -> Resolve Model -> Resolve Methodology
       -> Resolve Factors -> Energy/Water/Carbon Estimate
       -> Uncertainty Propagation -> Confidence -> EstimateResult
  -> Persistence (PostgreSQL via SQLAlchemy 2.x async + Alembic migrations)
```

Module boundaries follow `docs/ARCHITECTURE.md` section 5:

- `app/api/` - HTTP routes and dependency wiring only (thin controllers).
- `app/core/` - configuration, security, structured logging, error contract.
- `app/db/` - async engine/session and the shared declarative base.
- `app/models/` - SQLAlchemy persistence models.
- `app/schemas/` - Pydantic request/response contracts.
- `app/services/` - business services (auth, workloads, estimates, batch).
- `app/methodology/` - the estimation engine: validator, resolvers,
  per-metric estimators, uncertainty aggregation, confidence, and the
  pipeline that sequences them.
- `app/providers/` - the provider adapter abstraction (structural in this
  sprint; adapters do not call any provider API yet).

### Architecture notes / decisions made during implementation

The FRD lists `Estimate.workload_id` as required, but `/v1/estimate` and
`/v1/batch-estimate` are specified as *calculate* endpoints while only
`/v1/events` is specified as *persist*. Rather than making `workload_id`
nullable (which would weaken the schema for the one endpoint that does
persist), `/v1/estimate` and `/v1/batch-estimate` are fully **stateless**:
no `AIWorkload` or `Estimate` row is written, and their `estimate_id` /
`batch_id` values are generated but not stored. `/v1/events` is the only
endpoint that persists `AIWorkload` + `Estimate` rows, keeping
`Estimate.workload_id` required with no schema conflict. This also gives
the API a genuinely useful distinction: `/v1/estimate` is a
cheap/no-retention "what would this cost" calculator, while `/v1/events`
is the durable, auditable usage record.

No public endpoints exist yet for creating organizations, projects or API
keys - the sprint brief's endpoint list (`/health`, `/v1/estimate`,
`/v1/events`, `/v1/batch-estimate`, `/v1/providers`, `/v1/models`,
`/v1/methodology`) does not include account/project/key management, and
the PRD places "Developer accounts, projects, API keys" in Phase 2
(Developer Platform), not this sprint. Provisioning currently happens
through `scripts/seed.py` and the `ApiKeyService`/service-layer classes
directly; a future sprint should add the developer-facing management
endpoints.

Rate limiting is defined in the error contract (`RATE_LIMITED`) and in
`docs/FRD.md` section 23 as a future plan-configurable abstraction, but no
limiter is wired up in this sprint (the sprint brief's own security-test
list and Definition of Done do not include it either).

A session-aggregation *service* (FRD section 16) is intentionally not
built yet, per the sprint brief's explicit "do not over-engineer session
orchestration in Sprint 1." The `parent_workload_id` relationship and the
`UncertaintyEngine.aggregate()` primitive (additive min/max summation) are
in place for a future sprint to build a coding-agent session rollup on.

## Database

PostgreSQL via SQLAlchemy 2.x (async, `asyncpg` driver) and Alembic
migrations (sync, `psycopg` driver, derived from the same `DATABASE_URL`).
`Base.metadata.create_all()` is never used as a schema-management
mechanism - all schema changes go through Alembic revisions.

Core tables: `organizations`, `projects`, `api_keys`, `providers`,
`models`, `methodologies`, `methodology_factors`, `ai_workloads`,
`estimates`.

`methodology_factors.provider` / `.model` are plain nullable strings, not
foreign keys - the data contract (`data/methodology/README.md`)
explicitly allows generic factors with no provider/model, and factors may
target research/hardware scopes with no corresponding registered
`Provider`/`Model` row.

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
> host's macOS version and could not be exercised here (see PR
> description for what was and wasn't verified). The Dockerfile/Compose
> file follow the standard FastAPI + Postgres pattern and were reviewed
> but not built in this sandbox - please verify `docker compose up --build`
> in CI or on a compatible machine before relying on it.

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
alembic revision --autogenerate -m "description"   # create a new migration
```

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

## Methodology principles

- Estimates are always **ranges** (`min`/`max`), never a single fabricated
  number, with `confidence`, `evidence_level`, `methodology_version` and
  `assumptions`.
- When no approved factor exists for a workload, the API returns an
  explicit `insufficient_data` status per metric rather than inventing a
  value.
- Methodology versions are immutable once published; historical estimates
  keep the methodology version used at calculation time.
- Aggregation (batches, future coding-agent sessions) sums minimums and
  sums maximums independently - it never averages a range into false
  precision.

See `docs/METHODOLOGY.md` for the full accounting-boundary, evidence-level
and confidence model.

## Security principles

- Raw API keys are never persisted - only a SHA-256 hash and a short,
  non-sensitive prefix for display/identification. The raw key is
  returned exactly once, at creation time.
- All protected endpoints require `Authorization: Bearer <API_KEY>`,
  resolved through API key -> Project -> Organization.
- Tenant isolation is enforced at the service layer: a workload in one
  organization can never be referenced (e.g. as a `parent_workload_id`)
  from another organization's API key.
- Errors follow a single consistent contract
  (`{"error": {"code", "message", "request_id"}}`) and never leak stack
  traces; every request gets a `request_id` (also returned as the
  `X-Request-ID` header) for log correlation.
- Structured JSON logs never contain API keys, secrets, prompts or
  generated content.
- No secrets are committed; configuration is environment-based
  (`.env`, git-ignored).

## Known limitations

- Methodology factors are not yet populated in the seed data (by design -
  see "No fabricated environmental factors" above).
- Provider adapters (`app/providers/`) are structural only; they do not
  call any provider API yet.
- No web frontend, mobile app or browser extension.
- No organization/project/API-key management endpoints yet (provisioning
  is via `scripts/seed.py` / service classes - see "Architecture notes").
- No rate limiting implementation yet (error code and abstraction point
  exist; no limiter is wired up).
- No coding-agent session aggregation endpoint yet (the
  `parent_workload_id` relationship and `UncertaintyEngine.aggregate()`
  primitive are in place for a future sprint).
- Docker Compose stack was authored and reviewed but could not be built
  in this sandbox (Docker Desktop was incompatible with the host macOS
  version); verify on a compatible machine or in CI before depending on it.
