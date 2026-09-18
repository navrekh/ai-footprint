# CLI integration tests

These tests run the real `aifootprint` console script's `main()` in
process against a real, locally started instance of the backend
(`backend/footprint-api`), backed by a real Postgres database - the
same approach `sdk/tests/integration/` uses. They are **not** part of
the default test run:

```bash
pytest                    # unit/contract tests only (fast, no external process)
pytest -m integration     # this directory only
```

## Requirements

Identical to the SDK's own integration tests (see
`sdk/tests/integration/README.md`):

- A local Postgres reachable at `CLI_INTEGRATION_DATABASE_URL` (defaults
  to a dedicated `footprint_cli_integration_test` database, created
  automatically if missing - deliberately separate from both the
  backend's own `footprint_test` and the SDK's own
  `footprint_sdk_integration_test`, for the same reason: these tests
  commit real rows through real HTTP requests rather than rolling back
  in a per-test transaction).
- The backend's virtualenv present at `../../../backend/footprint-api/.venv`.

## Scope

Covers: event success, estimate success, usage success, compare
success, benchmark success, authentication failure, authorization
failure, validation failure, transport failure, JSON output, and
non-interactive execution (environment-variable-only configuration, no
CLI flags, no local config file).

Rate-limit and generic server-failure scenarios are exercised against a
**mocked** SDK response instead of this live backend (see
`tests/test_estimate_command.py`/`tests/test_exit_codes.py`) - the real
backend does not implement rate limiting as of this sprint (see
`backend/footprint-api/README.md`'s Known Limitations) and there is no
reliable, non-destructive way to make it return a real 5xx on demand.
