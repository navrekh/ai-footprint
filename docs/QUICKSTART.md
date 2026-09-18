# AI Footprint — Quick Start

Get your first footprint estimate in about 10 minutes. No knowledge of
this repository's internals is required — just an HTTP client.

Every example below sends the exact same six requests three ways
(`curl`, Python's `requests`, and JavaScript's `fetch`), so pick whichever
matches how you'll actually integrate.

> **About the JavaScript examples:** they run as shown in Node.js (or
> any non-browser JS runtime), which isn't subject to browser CORS
> restrictions. Pasted into an arbitrary browser tab's console instead,
> they will be silently blocked unless that page's origin is explicitly
> present in the API's `ALLOWED_ORIGINS` — this API's CORS policy
> (`backend/footprint-api/README.md`'s "CORS" section) rejects
> cross-origin browser requests from any other origin by design. Don't
> expect these snippets to work from a random webpage's console.

## 0. Get a base URL

This backend does not yet have a hosted, shared endpoint (see
`docs/PRD.md`/`docs/FRD.md` — a production deployment is explicitly out
of scope through Sprint 5). Run it locally:

```bash
cd backend/footprint-api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
createdb footprint            # or: docker compose up --build
alembic upgrade head
python -m scripts.seed --with-test-only-demo-data   # so step 3 returns a real, non-insufficient_data estimate
uvicorn app.main:app --reload
```

See `backend/footprint-api/README.md` for the full setup reference
(Docker, environment variables, migrations). Every example on this page
uses:

```text
BASE_URL = http://localhost:8000
```

Swap it for wherever you've deployed the API — nothing below is
localhost-specific otherwise.

> The `--with-test-only-demo-data` seed creates one model
> (`test-only-demo-model` under provider `openai`) with clearly-labeled
> `TEST_ONLY` factors, purely so this walkthrough returns a measured
> result instead of `insufficient_data`. Never run that flag against a
> shared, staging, or production database — see "No fabricated
> environmental factors" in the backend README.

## 1. Sign up: create an organization

`POST /v1/organizations` is the one endpoint that needs no API key — it
bootstraps an Organization, a default Project, and your first API key in
one call. **The `api_key.key` field is shown exactly once, in this
response.** Save it now; the backend cannot show it to you again.

> **Keep your API key safe.** Never commit it to source control, never
> put it in a URL or query string, and never store it in a browser's
> `localStorage`/`sessionStorage`. The commands below deliberately keep
> the response in a shell variable only — nothing is written to a file
> on disk, so there's nothing to accidentally `git add`.

**curl**

```bash
SIGNUP=$(curl -s -X POST "$BASE_URL/v1/organizations" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Inc"}')
echo "$SIGNUP"

export API_KEY=$(echo "$SIGNUP" | python3 -c "import json,sys; print(json.load(sys.stdin)['api_key']['key'])")
export PROJECT_ID=$(echo "$SIGNUP" | python3 -c "import json,sys; print(json.load(sys.stdin)['project']['id'])")
```

**Python (`requests`)**

```python
import requests

BASE_URL = "http://localhost:8000"

response = requests.post(f"{BASE_URL}/v1/organizations", json={"name": "Acme Inc"})
response.raise_for_status()
signup = response.json()

api_key = signup["api_key"]["key"]        # save this now - shown only once
project_id = signup["project"]["id"]
print(f"API key: {api_key}")
print(f"Project: {project_id}")
```

**JavaScript (`fetch`)**

```javascript
const BASE_URL = "http://localhost:8000";

const response = await fetch(`${BASE_URL}/v1/organizations`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "Acme Inc" }),
});
const signup = await response.json();

const apiKey = signup.api_key.key; // save this now - shown only once
const projectId = signup.project.id;
console.log("API key:", apiKey);
console.log("Project:", projectId);
```

## 2. Create an application

Applications group workloads by product/service/environment within a
project. This step is optional (workloads work without one), but the
target developer journey includes it.

**curl**

```bash
APPLICATION=$(curl -s -X POST "$BASE_URL/v1/applications" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "My First App"}')
echo "$APPLICATION"

export APPLICATION_ID=$(echo "$APPLICATION" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
```

**Python (`requests`)**

```python
response = requests.post(
    f"{BASE_URL}/v1/applications",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"name": "My First App"},
)
response.raise_for_status()
application_id = response.json()["id"]
```

**JavaScript (`fetch`)**

```javascript
const appResponse = await fetch(`${BASE_URL}/v1/applications`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ name: "My First App" }),
});
const { id: applicationId } = await appResponse.json();
```

## 3. Send your first workload and receive a footprint

`POST /v1/events` persists the workload and returns its estimate
immediately. Every field below except `provider`/`model`/`modality`/
`activity_type` is optional.

**curl**

```bash
EVENT=$(curl -s -X POST "$BASE_URL/v1/events" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "application_id": "'"$APPLICATION_ID"'",
    "provider": "openai",
    "model": "test-only-demo-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 2000,
    "output_tokens": 1000,
    "idempotency_key": "quickstart-first-event"
  }')
echo "$EVENT"

export WORKLOAD_ID=$(echo "$EVENT" | python3 -c "import json,sys; print(json.load(sys.stdin)['workload_id'])")
```

**Python (`requests`)**

```python
response = requests.post(
    f"{BASE_URL}/v1/events",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "project_id": project_id,
        "application_id": application_id,
        "provider": "openai",
        "model": "test-only-demo-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 2000,
        "output_tokens": 1000,
        "idempotency_key": "quickstart-first-event",
    },
)
response.raise_for_status()
event = response.json()
print(event)
# {"event_id": "evt_...", "workload_id": "evt_...", "estimate_id": "est_...",
#  "status": "measured", "idempotent_replay": false}
```

**JavaScript (`fetch`)**

```javascript
const eventResponse = await fetch(`${BASE_URL}/v1/events`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    project_id: projectId,
    application_id: applicationId,
    provider: "openai",
    model: "test-only-demo-model",
    modality: "text",
    activity_type: "text_generation",
    input_tokens: 2000,
    output_tokens: 1000,
    idempotency_key: "quickstart-first-event",
  }),
});
const event = await eventResponse.json();
console.log(event);
```

`status` is `"measured"`, `"partial"`, or `"insufficient_data"` — never a
fabricated number when methodology data is missing. Resubmitting the
same request with the same `idempotency_key` returns this exact same
response again (`idempotent_replay: true`), rather than creating a
second measurement — safe to retry after a timeout.

Look up the persisted result any time with
`GET /v1/workloads/{workload_id}` or `GET /v1/estimates/{estimate_id}`
(both from the response above), using the same `Authorization` header.

## 4. View usage

**curl**

```bash
curl -s "$BASE_URL/v1/usage/summary" -H "Authorization: Bearer $API_KEY"
```

**Python (`requests`)**

```python
response = requests.get(f"{BASE_URL}/v1/usage/summary", headers={"Authorization": f"Bearer {api_key}"})
print(response.json())
```

**JavaScript (`fetch`)**

```javascript
const usage = await fetch(`${BASE_URL}/v1/usage/summary`, {
  headers: { Authorization: `Bearer ${apiKey}` },
}).then((r) => r.json());
console.log(usage);
```

The response reports total/measured/partial/insufficient-data workload
counts, measurement coverage, and additive energy/water/carbon ranges
for the trailing 30 days by default — never a false point estimate, and
never silently treating an unmeasured workload as zero impact.

## 5. Compare a workload across candidates

`POST /v1/compare` runs the *same* workload definition through multiple
provider/model candidates, each evaluated **independently**. Every
candidate keeps its own range, status, confidence, and methodology
version in the response — nothing is aggregated across candidates, and
the response never declares a "winner," "best," or recommended model.
You decide.

The example below sends the same `test-only-demo-model` candidate
twice, purely to demonstrate the request/response contract without
requiring a second seeded model. It is **not** a real cross-provider
comparison — it exists only to show the shape of the response you'd get
back. A genuine comparison across different providers/models requires
distinct candidates that each have available methodology data (e.g. two
real models seeded with approved factors); with only the `TEST_ONLY`
demo model available locally, that isn't possible in this walkthrough.

**curl**

```bash
curl -s -X POST "$BASE_URL/v1/compare" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 2000,
    "output_tokens": 1000,
    "candidates": [
      {"provider": "openai", "model": "test-only-demo-model"},
      {"provider": "openai", "model": "test-only-demo-model"}
    ]
  }'
```

**Python (`requests`)**

```python
response = requests.post(
    f"{BASE_URL}/v1/compare",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 2000,
        "output_tokens": 1000,
        "candidates": [
            {"provider": "openai", "model": "test-only-demo-model"},
            {"provider": "openai", "model": "test-only-demo-model"},
        ],
    },
)
print(response.json())
```

**JavaScript (`fetch`)**

```javascript
const compare = await fetch(`${BASE_URL}/v1/compare`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    modality: "text",
    activity_type: "text_generation",
    input_tokens: 2000,
    output_tokens: 1000,
    candidates: [
      { provider: "openai", model: "test-only-demo-model" },
      { provider: "openai", model: "test-only-demo-model" },
    ],
  }),
}).then((r) => r.json());
console.log(compare);
```

## Where to go next

- **Full API reference:** `GET /docs` (Swagger UI) on your running
  instance, or `GET /openapi.json` for the raw schema — every endpoint,
  request/response shape, and possible error is documented there.
- **Error handling, request IDs, idempotency details, CORS policy:**
  `backend/footprint-api/README.md`.
- **Standardized benchmarks** (`GET /v1/benchmarks`,
  `POST /v1/benchmarks/run`): reproducible workload definitions you can
  run against any provider/model without hand-writing the workload
  fields yourself.
- **Product/methodology background:** `docs/PRD.md`, `docs/FRD.md`,
  `docs/METHODOLOGY.md`.
