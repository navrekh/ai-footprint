# Integration tests

These tests run the real `aifootprint` SDK over real HTTP against a real,
locally started instance of the backend (`backend/footprint-api`), backed
by a real Postgres database. They are **not** part of the default test
run:

```bash
pytest                    # unit tests only (fast, no external process)
pytest -m integration     # this directory only
```

## Requirements

- A local Postgres reachable at `SDK_INTEGRATION_DATABASE_URL` (defaults
  to `postgresql+asyncpg://footprint:footprint@localhost:5432/footprint_sdk_integration_test`
  — a dedicated database, created automatically if missing, and
  deliberately **not** the backend's own `footprint_test`).
- The backend's virtualenv present at `../../backend/footprint-api/.venv`
  with its dependencies installed (`pip install -e ".[dev]"` from that
  directory). If it's missing, these tests are skipped rather than failed.

## What the fixtures do

`live_backend_url` (session-scoped) creates `footprint_sdk_integration_test`
if it doesn't exist, runs `alembic upgrade head`, runs
`scripts/seed.py --with-test-only-demo-data` (idempotent — seeds the
`openai` / `test-only-demo-model` fixture data used by these tests), then
starts `uvicorn app.main:app` as a subprocess on a free local port and
waits for `/health` to respond before yielding the base URL. The server
is terminated at the end of the session.

`bootstrapped_org` (session-scoped) creates a fresh organization, project,
and API key via the SDK's own `client.organizations.create()` call, so
these tests never depend on or mutate the backend's `Demo Organization`
seed data.

**Why a separate database:** unlike the backend's own test suite (which
wraps each test in a transaction it always rolls back), these tests make
real HTTP calls to a real running server, which commits real rows through
its normal, non-test code path. Pointing this at the backend's shared
`footprint_test` database would leave committed rows behind that the
backend's own tests don't expect and can collide with (e.g. a duplicate
`providers` row) - this happened once during Sprint 5B development and
was fixed by giving these tests their own database rather than trying to
clean up after every run. Rows are left in `footprint_sdk_integration_test`
between runs; it's disposable and only ever used by this test file.
