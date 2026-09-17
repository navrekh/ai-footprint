# AI FOOTPRINT
## Functional Requirements Document (FRD)
### Version 0.1 — MVP

**Status:** Foundation draft  
**Purpose:** Implementation contract for the AI Footprint MVP.

## 1. System Components

- API Layer: FastAPI
- Authentication/API key layer
- Workload processing service
- Footprint estimation engine
- Methodology registry
- Provider/model registry
- Usage metering
- PostgreSQL persistence
- Developer dashboard (later phase)

## 2. Core Domain Object — AIWorkload

Required:
- id
- organization_id
- project_id
- provider
- model
- modality
- activity_type
- timestamp

Optional:
- input_tokens
- output_tokens
- image_count
- image_width
- image_height
- video_seconds
- video_resolution
- audio_seconds
- tool_calls
- duration_seconds
- parent_workload_id
- metadata

## 3. Activity Types

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

## 4. Organization and Project Model

### Organization
- id
- name
- created_at
- updated_at

### Project
- id
- organization_id
- name
- created_at
- updated_at

Every workload belongs to a project and organization.

## 5. API Key Model

Fields:
- id
- project_id
- key_hash
- key_prefix
- name
- status
- created_at
- last_used_at
- revoked_at

Raw API keys must never be persisted.

## 6. Provider Registry

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

## 7. Model Registry

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

Historical estimates must preserve the model/methodology version used at calculation time.

## 8. Methodology Registry

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

## 9. Methodology Factors

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

## 10. Estimation Pipeline

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

Each stage should be independently testable.

## 11. Estimate Object

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

## 12. API Endpoints

### GET /health
Public health endpoint.

### POST /v1/estimate
Calculate a single workload estimate.

### POST /v1/events
Persist a workload event and create an associated estimate when supported.

### POST /v1/batch-estimate
Calculate a bounded batch of workloads.

### GET /v1/providers
List providers.

### GET /v1/models
List models, filterable by provider/modality/status.

### GET /v1/methodology
Return methodology versions, scope, assumptions, limitations and sources.

Protected endpoints require API key authentication.

## 13. Estimate Request

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

## 14. Estimate Response

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

## 15. Insufficient Data

Where no defensible factor exists, the API must return an explicit unavailable/insufficient-data state rather than fabricating a number.

## 16. Coding and Agent Sessions

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

A session aggregation service shall calculate aggregate impact from supported child events.

## 17. Image Workloads

Where available, capture:
- model
- activity_type
- image_count
- width
- height
- inference_steps

## 18. Video Workloads

Where available, capture:
- model
- duration_seconds
- resolution
- frame_rate
- number_of_outputs

## 19. Audio Workloads

Where available, capture:
- model
- activity_type
- duration_seconds

## 20. Agentic Workloads

Support:
- parent session
- child inference events
- tool call count
- duration
- token usage

## 21. Aggregation

Support:
- daily
- weekly
- monthly
- custom date range

Aggregate water, energy and carbon as ranges. Do not collapse uncertainty into misleading precision.

## 22. Authentication and Authorization

API key → Project → Organization.

All protected resources must enforce organization isolation.

## 23. Rate Limiting

Rate limits must be plan-configurable. The implementation should provide an abstraction even if the first deployment uses a simple in-process or Redis-backed limiter.

## 24. Error Contract

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
- INTERNAL_ERROR

## 25. Privacy

The core API must not require prompt text, generated content, private images or source code.

Store workload metadata only when necessary for estimation, analytics, billing or security.

## 26. Security Requirements

- HTTPS only in deployed environments
- Hash API keys at rest
- Revoke/rotate keys
- Validate all inputs
- Tenant isolation
- Request IDs
- Structured logging
- Externalized secrets
- Least privilege
- Dependency/security scanning

## 27. Testing Requirements

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

### Integration
- authentication
- estimate
- events
- batch
- provider/model/methodology endpoints
- persistence
- tenant isolation

### Security
- invalid/revoked keys
- missing keys
- cross-tenant access
- malformed payloads
- rate limiting

### Regression
Same workload + same methodology version must produce the same estimate.

## 28. Non-Functional Requirements

Target MVP performance:
- p95 single estimate under 500 ms excluding external dependencies
- scalable stateless API workers
- health monitoring
- structured application logs
- environment separation: development, staging, production

## 29. Definition of Done

MVP backend foundation is complete when:

1. FastAPI starts successfully.
2. PostgreSQL migrations execute cleanly.
3. Organization/project/API key flows work.
4. API authentication works.
5. AIWorkload persistence works.
6. Provider and model registries work.
7. Methodology registry works.
8. Estimation engine has clean interfaces.
9. Unsupported data is handled safely.
10. Estimates are persisted.
11. Tenant isolation is tested.
12. OpenAPI documentation is generated.
13. Automated tests pass.
14. Docker environment works.
15. No environmental coefficients are fabricated.
16. Additional providers can be added without changing the core estimation architecture.
