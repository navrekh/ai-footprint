# aifootprint

A thin, typed Python client for the AI Footprint API. It sends HTTP
requests and parses the responses into typed objects — it does not
estimate, aggregate, rank, or otherwise duplicate anything the backend
already computes. The backend is always the source of truth.

- Python: `>=3.10`
- Dependencies: `httpx`, `pydantic` (v2)
- Sync only — no `asyncio` required to use this SDK

## Install

```bash
pip install aifootprint
```

(Or, from a local checkout of this repository: `pip install -e ./sdk`.)

## Configure your API key

Get an API key from your organization (`client.api_keys.create(...)`, or
one returned when you first sign up — see below). Then set it as an
environment variable rather than hardcoding it:

```bash
export AIFOOTPRINT_API_KEY="afp_..."
export AIFOOTPRINT_BASE_URL="https://your-ai-footprint-instance.example.com"
```

**Never commit an API key to source control.** The SDK never logs,
prints, or writes your key to disk on its own — it only ever sends it as
an `Authorization: Bearer <key>` header.

Configuration precedence (for both the API key and the base URL):

1. an explicit constructor argument (`AIClient(api_key=..., base_url=...)`)
2. the environment variable (`AIFOOTPRINT_API_KEY` / `AIFOOTPRINT_BASE_URL`)
3. a documented default — `base_url` only, `http://localhost:8000` (a
   local-development convenience; there is no hosted AI Footprint
   instance, so real usage should always set this explicitly)

## Create a client

```python
from aifootprint import AIClient

client = AIClient()  # reads AIFOOTPRINT_API_KEY / AIFOOTPRINT_BASE_URL
```

`AIClient` owns one underlying HTTP connection pool. Close it when you're
done, or use it as a context manager:

```python
with AIClient() as client:
    ...  # client.close() is called automatically, even on exception
```

### First time? Create an organization

If you don't have an API key yet, `organizations.create()` requires no
authentication and returns everything you need to get started:

```python
from aifootprint import AIClient

with AIClient(base_url="http://localhost:8000") as anon_client:
    bootstrap = anon_client.organizations.create(name="My Company")

print(bootstrap.organization.id)
print(bootstrap.project.id)
print(bootstrap.api_key.key)  # save this now - it is shown exactly once
```

## Your first estimate

`client.estimates.create(...)` is **stateless** — it computes a resource
impact estimate on the fly and returns it. Nothing is persisted or
associated with your account; call it as many times as you like to
explore "what if" scenarios.

```python
estimate = client.estimates.create(
    provider="openai",
    model="model-id",
    modality="text",
    activity_type="text_generation",
    input_tokens=2000,
    output_tokens=1000,
)

print(estimate.energy.min, estimate.energy.max, estimate.energy.unit)
print(estimate.confidence, estimate.methodology_version)
```

## Recording an event (persistent)

`client.events.create(...)` is the **persistent** counterpart to
`estimates.create()` — it records a real workload against your project
(optionally an application), computes its estimate, and stores both so
they show up in usage queries later.

```python
event = client.events.create(
    provider="openai",
    model="model-id",
    modality="text",
    activity_type="text_generation",
    input_tokens=2000,
    output_tokens=1000,
    project_id="proj_...",
    application_id="app_...",       # optional
    idempotency_key="checkout-session-42",  # optional but recommended
)

print(event.workload_id, event.estimate_id, event.status)
```

### Idempotency

`idempotency_key` is an ordinary field on the request body (not an HTTP
header). If you call `events.create()` twice with the same key, the
second call returns the **original** result unchanged
(`event.idempotent_replay` is `True`) instead of recording a duplicate
workload — safe to use when retrying a request after a timeout or
uncertain response. The SDK never generates one for you; if you omit it,
no idempotency key is sent, and a retry will record a second, distinct
event.

### Client / integration metadata

Both `estimates.create()` and `events.create()` accept an optional
`client` argument identifying the software surface instrumenting the
workload — distinct from `application_id`, which identifies the
product/service/environment that *owns* it. It is purely observational:
submitting different client metadata for an otherwise identical
workload never changes the resulting estimate.

```python
from aifootprint import ClientContext, ClientType

event = client.events.create(
    provider="openai",
    model="model-id",
    modality="text",
    activity_type="text_generation",
    input_tokens=2000,
    output_tokens=1000,
    project_id="proj_...",
    client=ClientContext(
        client_type=ClientType.PYTHON_SDK,
        client_name="my-backend-service",
        client_version="1.4.0",
    ),
)
```

A plain `dict` (e.g. `client={"client_type": "python_sdk"}`) works too —
`ClientContext` is a convenience, not a requirement. Omitting `client`
entirely keeps working exactly as before Sprint 6.

## Querying usage

Usage figures are **derived from previously persisted events** — they
reflect what you've recorded via `events.create()` (or the batch
endpoint), not stateless calls to `estimates.create()`.

```python
summary = client.usage.summary()
print(summary.workloads.total, summary.workloads.coverage_percent)
print(summary.energy.min, summary.energy.max)

by_provider = client.usage.by_provider(limit=10)
for item in by_provider.items:
    print(item.provider, item.workloads.total)

timeseries = client.usage.timeseries(granularity="day")
```

## Running a comparison

`client.compare.create(...)` evaluates the same workload across multiple
provider/model candidates and returns each candidate's result
independently, in the order given. **The SDK never ranks, scores, or
picks a "winner"** — if you want to compare numbers, read the ranges
yourself.

```python
result = client.compare.create(
    modality="text",
    activity_type="text_generation",
    input_tokens=2000,
    output_tokens=1000,
    candidates=[
        {"provider": "openai", "model": "model-a"},
        {"provider": "anthropic", "model": "model-b"},
    ],
)

for item in result.results:
    if item.status == "success":
        print(item.candidate.provider, item.estimate.energy.min, item.estimate.energy.max)
    else:
        print(item.candidate.provider, "failed:", item.error.message)
```

## Querying a benchmark

Benchmarks are fixed, versioned scenario definitions maintained by the
backend. `benchmarks.run()` behaves like `compare.create()` — independent
per-candidate results, no ranking:

```python
definitions = client.benchmarks.list(activity_type="text_generation")
definition = client.benchmarks.get(definitions.items[0].benchmark_id)

run = client.benchmarks.run(
    definition.benchmark_id,
    candidates=[{"provider": "openai", "model": "model-a"}],
)
```

## Handling errors

Every non-2xx response raises a typed exception — never a raw `httpx`
exception — with the HTTP status, the API's error code, the message, and
the request ID attached:

```python
from aifootprint import APIError, NotFoundError, ValidationError

try:
    client.projects.get("proj_does_not_exist")
except NotFoundError as e:
    print(e.status_code, e.code, e.message, e.request_id)
except ValidationError as e:
    print("bad request:", e.message)
except APIError as e:
    # catch-all for any other 4xx/5xx not covered above
    print(e.status_code, e.message)
```

Exception hierarchy: `AIFootprintError` (base) →
`TransportError` (network/timeout failures — no HTTP response at all) and
`APIError` (the backend returned a non-2xx response), with `APIError`
further specialized into `AuthenticationError` (401), `AuthorizationError`
(403), `ValidationError` (400/422), `NotFoundError` (404),
`ConflictError` (409), and `RateLimitError` (429).

## Request IDs

Every successful call's result carries the server's `X-Request-ID` as
`result.request_id` — hand this to support when reporting an issue. A
failed call carries the same value on the raised exception instead
(`exception.request_id`), so there is exactly one place to look either
way.

The one exception: `client.providers.list()`, `client.models.list()`, and
`client.methodology.list()` return plain Python lists (mirroring the
backend, which returns a bare JSON array for these three endpoints), so
there's no object to attach a request ID to.

## Ranges, confidence, and uncertainty

AI Footprint estimates are **ranges**, never single numbers — this SDK
never averages `min`/`max` into a point value, and never rounds partial
coverage up to imply completeness. Every estimate also carries:

- `status` — `"ok"`, `"partial"`, or `"insufficient_data"`
- `confidence` — `"high"`, `"medium"`, or `"low"`
- `methodology_version` and `assumptions` — what produced this number and
  under what assumptions
- for aggregated usage figures, `measured_workloads` / `total_workloads`
  — so a partial result is never indistinguishable from a complete one

Always check `status` before treating a range as meaningful, especially
for new or rarely-used provider/model combinations.

## Development

```bash
cd sdk
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                 # unit tests (fast, no external services)
pytest -m integration  # integration tests against a real local backend -
                        # see tests/integration/README.md
ruff check aifootprint tests
mypy aifootprint
```
