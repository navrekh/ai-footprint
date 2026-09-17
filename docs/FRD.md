# AI FOOTPRINT
## Functional Requirements Document (FRD)
### Version 0.2 — Foundation + Developer Platform

**Status:** Approved — Sprint 3 implementation contract  
**Purpose:** Define the functional and technical requirements for the AI Footprint backend through the Developer Platform & Usage Intelligence milestone.

## 1. System Components

- API Layer: FastAPI
- Authentication/API key layer
- Organization/project/application management
- Workload processing service
- Footprint estimation engine
- Methodology registry
- Provider/model registry
- Usage aggregation service
- PostgreSQL persistence
- Audit/request metadata
- Developer dashboard: later UI phase consuming these APIs

## 2. Domain Hierarchy

```text
Organization
  └── Project
       └── Application
            ├── API Keys
            └── AI Workloads
                 └── Estimates
```

### Organization
Top-level tenant and security boundary.

### Project
Operational boundary within an organization and primary future billing boundary.

### Application
A named AI product, service, environment or workload source belonging to exactly one project.

### API Key
Authentication credential. Initial scopes remain organization-level and project-level. Application-scoped keys are deferred.

### AIWorkload
The fundamental measurement object representing an AI activity or workload event.

### Estimate
The environmental/resource estimate associated with a workload.

## 3. Application Model

Application fields:

- id
- project_id
- name
- slug
- description
- status
- environment
- created_at
- updated_at

Allowed initial status values:

- active
- inactive

Allowed environment values when supplied:

- development
- staging
- production

Requirements:

1. Application slug must be unique within its project.
2. Application must belong to an existing project.
3. A workload may reference an application only when that application belongs to the workload's project.
4. Application reads and writes must enforce organization and project authorization.
5. Deactivating an application must not delete historical workloads or estimates.
6. Historical workloads must retain their application association.

## 4. Core Domain Object — AIWorkload

Required:
- id
- organization_id
- project_id
- provider
- model
- modality
- activity_type
- timestamp

Sprint 3 addition:
- application_id: nullable for backward compatibility with existing workloads; when supplied it must belong to the workload's project.

Optional:
- input_tokens
- output_tokens
- input_chars
- output_chars
- image_count
- image_width
- image_height
- inference_steps
- video_seconds
- video_resolution
- frame_rate
- number_of_outputs
- audio_seconds
- tool_calls
- duration_seconds
- parent_workload_id
- metadata

## 5. Activity Types

Initial values:
- text_generation
- text_reasoning
- image_generation
- image_editing
- image_enhancement
- video_generation
- audio_generation
- speech_to_text
- vision
- code_generation
- code_review
- debugging
- test_generation
- code_refactoring
- coding_agent
- embedding
- rag
- classification
- agent_workflow

The calculation engine must not hard-code provider-specific logic into activity controllers.

## 6. Organization and Project Model

### Organization
- id
- name
- slug
- status
- created_at
- updated_at

### Project
- id
- organization_id
- name
- slug
- description
- status
- created_at
- updated_at

Every workload belongs to a project and organization.

Every application belongs to exactly one project.

## 7. API Key Model

Fields:
- id
- organization_id
- project_id: nullable for organization-level keys
- key_hash
- key_prefix
- name
- status
- expires_at
- created_at
- last_used_at
- revoked_at

Rules:

1. Raw API keys must never be persisted.
2. API keys are returned only at creation time.
3. Expired and revoked keys must not authorize protected requests.
4. Project-scoped keys may access only their project.
5. Organization-level keys may access projects within their organization subject to endpoint rules.
6. Single-record endpoints must enforce the same project boundary as collection endpoints.

## 8. Provider Registry

Provider fields:
- id
- name
- status
- supported_modalities
- created_at
- updated_at

Initial providers:
- openai
- anthropic
- google

Supported statuses:
- active
- beta
- deprecated

## 9. Model Registry

Fields:
- id
- provider_id
- name
- version
- modalities
- status
- methodology_version
- effective_from
- effective_to

Historical estimates must preserve the model and methodology version used at calculation time.

## 10. Methodology Registry

Fields:
- methodology_id
- version
- description
- effective_date
- sources
- assumptions
- limitations
- created_at

Published methodology versions are immutable.

## 11. Methodology Factors

Fields:
- factor_id
- metric
- provider
- model
- modality
- activity_type
- region
- hardware
- value_min
- value_max
- unit
- evidence_level
- confidence
- source
- source_date
- effective_from
- effective_to
- methodology_version
- assumptions
- limitations

Do not hard-code environmental factors in application source code.

A missing or non-authoritative factor must produce an explicit insufficient-data result rather than a fabricated coefficient.

## 12. Estimation Pipeline

```text
AIWorkload
→ Validate
→ Resolve provider
→ Resolve model
→ Resolve methodology
→ Estimate energy
→ Estimate water
→ Estimate carbon
→ Propagate uncertainty
→ Determine confidence
→ Persist Estimate
→ Return response
```

Each stage must be independently testable.

## 13. Estimate Object

Fields:
- estimate_id
- workload_id
- energy_min_wh
- energy_max_wh
- water_min_ml
- water_max_ml
- carbon_min_g
- carbon_max_g
- confidence
- evidence_level
- methodology_version
- assumptions
- created_at

## 14. API Endpoints — Foundation

### GET /health
Public health endpoint.

### POST /v1/estimate
Calculate a single workload estimate. This endpoint remains stateless.

### POST /v1/events
Persist a workload event and create an associated estimate when supported. Idempotency is supported using the project and idempotency key.

### POST /v1/batch-estimate
Calculate a bounded batch of workloads. This endpoint remains stateless.

### GET /v1/providers
List providers.

### GET /v1/models
List models, filterable by provider/modality/status.

### GET /v1/methodology
Return methodology versions, scope, assumptions, limitations and sources.

Protected endpoints require API key authentication.

## 15. API Endpoints — Application Management

### POST /v1/applications
Create an application within an authorized project.

Required request fields:
- project_id where required by credential scope
- name

Optional:
- slug
- description
- status
- environment

The service shall generate a safe slug when omitted or reject a conflicting explicit slug.

### GET /v1/applications
List applications visible to the authenticated organization/project. Support project filtering and bounded pagination.

### GET /v1/applications/{application_id}
Return an application only when it belongs to the authorized organization and, for project-scoped credentials, the authorized project.

### PATCH /v1/applications/{application_id}
Update mutable application fields without changing ownership.

## 16. API Endpoints — Usage Intelligence

### GET /v1/usage/summary
Return aggregate workload counts, measurement coverage and energy/water/carbon ranges for a requested period and authorized scope.

Conceptual response:

```json
{
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "workloads": {
    "total": 10000,
    "measured": 7500,
    "partial": 2500,
    "coverage_percent": 75.0
  },
  "energy": {
    "status": "partial",
    "min_wh": 42.8,
    "max_wh": 51.2,
    "unit": "Wh"
  },
  "water": {
    "status": "partial",
    "min_ml": 1284,
    "max_ml": 1590,
    "unit": "mL"
  },
  "carbon": {
    "status": "partial",
    "min_g": 17.6,
    "max_g": 22.1,
    "unit": "gCO2e"
  }
}
```

### GET /v1/usage/by-provider
Return aggregate workload counts, coverage and resource ranges grouped by provider.

### GET /v1/usage/by-model
Return aggregate workload counts, coverage and resource ranges grouped by provider/model/version as appropriate.

### GET /v1/usage/by-activity
Return aggregate workload counts, coverage and resource ranges grouped by activity type.

### GET /v1/usage/by-application
Return aggregate workload counts, coverage and resource ranges grouped by application.

### GET /v1/usage/timeseries
Return aggregate resource ranges and workload counts by time bucket.

Supported initial granularities:
- day
- week
- month

All usage endpoints must support an explicit date range. Project and application filters are supported where applicable.

## 17. Usage Aggregation Semantics

Usage data shall be derived from persisted AIWorkload and Estimate records in PostgreSQL for the initial implementation.

Do not create a separate synchronized usage ledger or materialized usage table in Sprint 3.

### Workload counts

- `total`: all workloads matching the authorized scope and date range.
- `measured`: workloads with a defensible estimate for the relevant metric(s).
- `partial`: workloads where some requested resource metrics or methodology coverage are incomplete.
- `insufficient_data`: workloads without a defensible estimate.

### Measurement coverage

Coverage percentage is based on the workload population and must be explicit.

For example:

```text
10,000 total workloads
7,500 measured workloads
= 75% measurement coverage
```

The remaining 2,500 workloads must not silently contribute fabricated values to aggregate metrics.

### Range aggregation

For each metric:

```text
aggregate_min = sum(individual_min)
aggregate_max = sum(individual_max)
```

The API must preserve the range and must not replace it with a false point estimate.

### Aggregate status

Initial statuses:
- `ok`: all relevant workloads have defensible data for the requested metric.
- `partial`: some workloads or metrics lack complete methodology coverage.
- `insufficient_data`: no defensible data exists for the requested aggregate metric.

## 18. Usage Filtering and Authorization

Every usage query must apply authorization before aggregation.

Required rules:

1. Organization-level credentials may aggregate across projects in their organization.
2. Project-scoped credentials may aggregate only their project.
3. Application filters must reference an application belonging to the authorized project/organization.
4. A cross-tenant application, project or workload must not affect counts or aggregates.
5. Invalid scope references must fail safely without revealing whether another tenant's resource exists.
6. Date ranges must be validated and bounded.
7. High-cardinality breakdown endpoints must use bounded pagination or another explicit result-size limit.

## 19. Estimate Request

Example:

```json
{
  "provider": "openai",
  "model": "model-id",
  "modality": "text",
  "activity_type": "text_generation",
  "input_tokens": 2000,
  "output_tokens": 1000
}
```

Application-aware workload submissions may include:

```json
{
  "project_id": "proj_xxx",
  "application_id": "app_xxx",
  "provider": "openai",
  "model": "model-id",
  "modality": "text",
  "activity_type": "text_generation",
  "input_tokens": 2000,
  "output_tokens": 1000
}
```

The service must verify that `application_id` belongs to the supplied/authorized project.

## 20. Estimate Response

Example schema:

```json
{
  "estimate_id": "est_xxx",
  "energy": {
    "min_wh": 0,
    "max_wh": 0,
    "unit": "Wh"
  },
  "water": {
    "min_ml": 0,
    "max_ml": 0,
    "unit": "mL"
  },
  "carbon": {
    "min_g": 0,
    "max_g": 0,
    "unit": "gCO2e"
  },
  "confidence": "medium",
  "evidence_level": 3,
  "methodology_version": "0.1",
  "assumptions": []
}
```

Zeroes are schema placeholders only. The system must not invent environmental coefficients.

## 21. Insufficient Data

Where no defensible factor exists, the API must return an explicit unavailable/insufficient-data state rather than fabricating a number.

Insufficient data must remain distinguishable from zero consumption.

## 22. Coding and Agent Sessions

Coding-agent workloads support parent/child relationships.

Example:

```text
Coding session
 ├── inference
 ├── tool metadata
 ├── inference
 ├── inference
 └── inference
```

Child events reference `parent_workload_id`.

A session aggregation service shall calculate aggregate impact from supported child events. This is not expanded beyond the existing foundation requirements in Sprint 3.

## 23. Image Workloads

Where available, capture:
- model
- activity_type
- image_count
- width
- height
- inference_steps

## 24. Video Workloads

Where available, capture:
- model
- duration_seconds
- resolution
- frame_rate
- number_of_outputs

## 25. Audio Workloads

Where available, capture:
- model
- activity_type
- duration_seconds

## 26. Agentic Workloads

Support:
- parent session
- child inference events
- tool call count
- duration
- token usage

## 27. Authentication and Authorization

API key → Project → Organization.

Application adds a subordinate scope:

API key → Project → Application → Workload

All protected resources must enforce organization isolation. Project-scoped keys must never access another project, including through single-record endpoints.

## 28. Rate Limiting

Rate limits must be plan-configurable. The implementation should provide an abstraction even if the first deployment uses a simple in-process or Redis-backed limiter.

Rate limiting remains a platform concern and is not a mandatory Sprint 3 persistence feature unless required by the existing implementation.

## 29. Error Contract

Example:

```json
{
  "error": {
    "code": "MODEL_NOT_SUPPORTED",
    "message": "The requested model is not currently supported.",
    "request_id": "req_xxx"
  }
}
```

Initial error codes:
- INVALID_REQUEST
- INVALID_API_KEY
- UNAUTHORIZED
- FORBIDDEN
- PROVIDER_NOT_FOUND
- MODEL_NOT_FOUND
- MODEL_NOT_SUPPORTED
- INVALID_WORKLOAD
- MISSING_PARAMETER
- RATE_LIMITED
- METHODOLOGY_UNAVAILABLE
- APPLICATION_NOT_FOUND
- APPLICATION_PROJECT_MISMATCH
- INVALID_DATE_RANGE
- INTERNAL_ERROR

## 30. Privacy

The core API must not require prompt text, generated content, private images or source code.

Store workload metadata only when necessary for estimation, analytics, billing or security.

Usage APIs must operate on metadata and estimates and must not require AI content.

## 31. Security Requirements

- HTTPS only in deployed environments
- Hash API keys at rest
- Revoke/expire keys
- Validate all inputs
- Tenant isolation
- Project isolation
- Application ownership validation
- Request IDs
- Structured logging
- Externalized secrets
- Least privilege
- Dependency/security scanning
- Safe error responses
- No cross-tenant aggregation

## 32. Testing Requirements

### Unit
- validation
- provider resolution
- model resolution
- methodology resolution
- energy calculation
- water calculation
- carbon calculation
- uncertainty propagation
- confidence
- application validation
- usage aggregation
- coverage calculation
- range aggregation
- date-range validation

### Integration
- authentication
- estimate
- events
- batch
- provider/model/methodology endpoints
- persistence
- application CRUD
- workload/application association
- usage summary
- usage breakdowns
- usage time series
- tenant isolation
- project isolation

### Security
- invalid/revoked/expired keys
- missing keys
- cross-tenant access
- cross-project application access
- cross-project workload access
- malformed payloads
- unauthorized usage aggregation
- invalid application/project combinations
- rate limiting abstraction behavior where implemented

### Regression
Same workload + same methodology version must produce the same estimate.

Usage aggregation over the same immutable historical data and methodology version must produce deterministic results.

## 33. Non-Functional Requirements

Target MVP performance:
- p95 single estimate under 500 ms excluding external dependencies
- scalable stateless API workers
- health monitoring
- structured application logs
- environment separation: development, staging, production

Sprint 3 usage queries should remain bounded and use indexed PostgreSQL queries. No analytics warehouse is required.

## 34. Sprint 3 Definition of Done

Sprint 3 is complete when:

1. Application database migration executes cleanly.
2. Application CRUD works.
3. Application slug uniqueness is enforced per project.
4. Application/project/organization authorization is enforced.
5. AIWorkload supports optional application association.
6. Invalid application/project combinations are rejected.
7. Existing workloads without an application remain valid.
8. Usage summary endpoint works for explicit date ranges.
9. Provider/model/activity/application usage breakdowns work.
10. Daily/weekly/monthly time series works.
11. Measurement coverage is reported explicitly.
12. Aggregate ranges preserve minimum and maximum semantics.
13. Partial and insufficient-data states are preserved.
14. Usage queries enforce tenant and project isolation.
15. High-cardinality responses are bounded.
16. OpenAPI documentation is generated.
17. Unit, integration and security tests pass.
18. No environmental coefficients are fabricated.
19. No separate synchronized usage ledger is introduced.
20. Existing Sprint 1 and Sprint 2 behavior remains backward compatible except where stricter authorization is intentionally enforced.

## 35. Overall MVP Definition of Done

MVP backend foundation is complete when:

1. FastAPI starts successfully.
2. PostgreSQL migrations execute cleanly.
3. Organization/project/API key flows work.
4. API authentication works.
5. AIWorkload persistence works.
6. Application management works.
7. Provider and model registries work.
8. Methodology registry works.
9. Estimation engine has clean interfaces.
10. Unsupported data is handled safely.
11. Estimates are persisted.
12. Usage intelligence APIs are available.
13. Tenant isolation is tested.
14. OpenAPI documentation is generated.
15. Automated tests pass.
16. Docker environment works.
17. No environmental coefficients are fabricated.
18. Additional providers can be added without changing the core estimation architecture.
