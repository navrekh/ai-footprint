# aifootprint-cli

The command-line client for the [AI Footprint](../README.md) API. It is
a thin wrapper around the existing `aifootprint` Python SDK - every
command it exposes calls `AIClient`, which is the sole HTTP and
authentication boundary. This package contains no estimation,
methodology, or ranking logic of its own.

```text
aifootprint CLI -> Python SDK (aifootprint) -> AI Footprint REST API
```

## Install

Not yet published to PyPI — publishing is implemented (wheel/sdist build,
clean-environment install verified, [trusted-publishing workflow](../docs/RELEASING.md)
in place) but no release has been tagged yet. Once published, a plain
`pip install aifootprint-cli` will pull in a compatible `aifootprint` SDK
automatically (see `docs/RELEASING.md`'s versioning policy) — no separate
SDK install step, no editable install, no repository checkout required.

Until then, install from a local checkout of this repository:

```bash
cd sdk && pip install -e .
cd ../cli && pip install -e .
```

Both installs are needed for local development: the CLI depends on the
SDK, and in this monorepo (pre-publish) that dependency is resolved via an
editable install rather than a published package version.

Requires Python 3.10+.

## Configure your API key

Create an organization (this is the same bootstrap call the console
and SDK use - see the root `README.md`'s Quick Start) to get your
first API key, then export it:

```bash
export AIFOOTPRINT_API_KEY="afp_live_..."
export AIFOOTPRINT_BASE_URL="http://localhost:8000"   # or https://api.aifootprint.tech in production
```

### Configuration precedence

For both the API key and base URL, in order:

1. an explicit command-line option (`--api-key` / `--base-url`)
2. an environment variable (`AIFOOTPRINT_API_KEY` / `AIFOOTPRINT_BASE_URL`)
3. a local, user-local configuration file
4. the SDK's own default behavior (no default for the API key; `http://localhost:8000` for the base URL)

The local configuration file lives at `$XDG_CONFIG_HOME/aifootprint/config.json`
(or `~/.config/aifootprint/config.json` when `XDG_CONFIG_HOME` is unset)
and, if present, is a plain JSON object:

```json
{
  "api_key": "afp_live_...",
  "base_url": "http://localhost:8000"
}
```

This file is **read-only** from the CLI's perspective in this release -
there is no `aifootprint config set` command yet (see "Known
limitations" below). Restrict its permissions yourself:

```bash
chmod 600 ~/.config/aifootprint/config.json
```

The CLI warns on stderr (but does not fail) if this file is readable
by anyone other than its owner, and never logs or prints its contents.

Interactive login is not part of this release - only non-interactive,
API-key-based authentication is supported, which is also what makes
the CLI safe to run in CI/CD.

## Your first estimate (stateless)

```bash
aifootprint estimate \
  --provider openai --model model-id \
  --modality text --activity-type text_generation \
  --input-tokens 2000 --output-tokens 1000
```

```text
Energy: 0.01–0.02 Wh
Water: 0.01–0.02 mL
Carbon: 0.001–0.002 gCO2e
Confidence: low
Evidence level: 6
Accounting boundary: A
Methodology version: TEST_ONLY-0.1
Request ID: req_...
```

Nothing is persisted - call this as many times as you like.

## Recording an event (persistent)

```bash
aifootprint event \
  --provider openai --model model-id \
  --modality text --activity-type text_generation \
  --input-tokens 2000 --output-tokens 1000 \
  --project proj_... \
  --idempotency-key checkout-session-42
```

`--idempotency-key` is passed straight through to the existing
`POST /v1/events` idempotency mechanism (see the backend README's
"Idempotency" section) - resubmitting the same key for the same
project returns the original result instead of creating a duplicate
measurement. The CLI does not implement any deduplication of its own.

Every event the CLI submits automatically carries [Sprint 6 client
metadata](../docs/FRD.md) identifying it as coming from this CLI:

```json
{
  "client_type": "cli",
  "client_name": "aifootprint-cli",
  "client_version": "0.1.0",
  "runtime": "python/3.13.0"
}
```

This is purely observational - it cannot affect authorization, project/
application ownership, or the resulting estimate.

## Usage commands

```bash
aifootprint usage summary
aifootprint usage by-provider
aifootprint usage by-model
aifootprint usage by-activity
aifootprint usage by-application   # does not accept --application - it IS the grouping
aifootprint usage timeseries --granularity week
```

All support `--from`, `--to`, `--project`, `--provider`, `--model`,
`--activity-type` (and `--application`, except on `by-application`
itself - matching the backend's own `/v1/usage/by-application`
contract, which does not accept that filter). Coverage
(`measured`/`partial`/`insufficient_data`) and min/max ranges are
always shown explicitly; nothing is averaged into a single number, and
insufficient data is always rendered as the literal text
"Insufficient data," never zero.

## Compare

```bash
aifootprint compare \
  --modality text --activity-type text_generation \
  --input-tokens 2000 --output-tokens 1000 \
  --candidate openai:model-a \
  --candidate anthropic:model-b:2026-01-01
```

`--candidate` is repeatable (`provider:model` or
`provider:model:model_version`), at least two required. Candidates are
always rendered in the exact order the API returned them - this
command never ranks, scores, sorts, or recommends a candidate.

## Benchmarks

```bash
aifootprint benchmarks list
aifootprint benchmarks get text_generation_standard
aifootprint benchmarks run text_generation_standard \
  --candidate openai:model-a --candidate openai:model-b
```

`run` shares the exact same independent, unranked rendering as
`compare`.

## JSON output

Every command supports `--output json` alongside the default
human-readable `--output table`:

```bash
aifootprint estimate ... --output json
```

JSON output is always valid, machine-parseable JSON on stdout with no
ANSI escape codes, reflects the API's own response shape exactly (via
the SDK's typed models), and never introduces a ranking, score, or
recommendation field. The request ID (when the API returned one) is
merged into the JSON body as `"request_id"`.

Errors are always printed as a concise message to **stderr** (never
mixed into stdout's JSON), so `--output json` piped to `jq` or parsed
by a script is always safe regardless of whether the command succeeded.

## CI/CD

The CLI requires no TTY, no browser, and no interactive confirmation.
A typical CI step:

```bash
AIFOOTPRINT_API_KEY="$SECRET" \
AIFOOTPRINT_BASE_URL="https://api.aifootprint.tech" \
aifootprint event --provider openai --model model-id \
  --modality text --activity-type text_generation \
  --input-tokens 2000 --output-tokens 1000 \
  --output json || exit "$?"
```

Branch on the exit code (see below) rather than parsing the
human-readable output.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 2 | invalid input / API validation |
| 3 | authentication failure |
| 4 | authorization failure |
| 5 | not found |
| 6 | conflict |
| 7 | rate limited |
| 8 | server/API failure |
| 9 | transport/network failure |
| 10 | configuration error |
| 1 | unexpected (programming) error - deliberately not one of the codes above |

Centralized in `aifootprint_cli/exit_codes.py`; every command dispatch
goes through the same mapping function.

## Request IDs

Shown as `Request ID: req_...` in human-readable output whenever the
API returned one, and preserved as `"request_id"` in JSON output. On
error, the request ID (when available) is printed to stderr - include
it when reporting an issue.

## Privacy

The CLI operates entirely on workload *metadata* - it never requires,
and never automatically collects, prompt text, model response text,
source code, private files/images/audio/video, browser data, cookies,
or third-party provider credentials. `--metadata` accepts an arbitrary
JSON object for your own bookkeeping (e.g. `{"env": "ci"}`) - never put
AI content in it.

## API-key security

The API key is never printed, logged, included in a URL, or embedded
in an exception message during normal operation. It is sent only as an
`Authorization: Bearer <key>` header by the SDK's transport layer -
this CLI never constructs that header itself. See
`tests/test_security.py` for the regression tests covering this.

## Known limitations

- No `aifootprint config` command to write the local configuration
  file yet - create `~/.config/aifootprint/config.json` by hand if you
  want that precedence layer. This is a deliberate Sprint 7 scope
  decision, not an oversight (see the Sprint 7 implementation report).
- `--metadata`/`--candidate` are the only structured input formats;
  there is no `--candidates-file` bulk option yet.

## Development

```bash
pip install -e ../sdk
pip install -e ".[dev]"
pytest                # unit/contract tests
pytest -m integration # requires a local backend + Postgres, see tests/integration/README.md
ruff check aifootprint_cli tests
mypy aifootprint_cli
```
