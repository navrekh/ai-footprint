# AI FOOTPRINT
## Architecture Decision Record / System Architecture
### Version 0.1

## 1. Architecture Goal

Build a provider-neutral AI resource impact measurement platform whose core capability is the estimation of energy, water and CO2e for AI workloads.

The architecture must support:

- multiple AI providers
- multiple modalities
- coding and agentic workloads
- methodology versioning
- uncertainty and confidence
- developer APIs and SDKs
- consumer applications
- enterprise integrations

without coupling the core estimation engine to a single provider or client application.

## 2. Core Principle

**AIWorkload is the canonical domain object.**

The platform does not model the product primarily as prompts. Prompts are one possible source of AIWorkload events.

## 3. Logical Architecture

```text
Clients
  |
  +-- Web
  +-- Mobile
  +-- Browser Extension
  +-- CLI
  +-- JS/Python SDK
  +-- Enterprise Gateway
  |
  v
API Layer / Authentication
  |
  v
Workload Service
  |
  +--> Provider Registry
  +--> Model Registry
  +--> Methodology Resolver
  |
  v
Footprint Engine
  |
  +--> Energy Estimator
  +--> Water Estimator
  +--> Carbon Estimator
  +--> Uncertainty Engine
  +--> Confidence Engine
  |
  v
Persistence / Analytics
```

## 4. Deployment Architecture

Initial AWS production-oriented design:

```text
Route 53
   |
CloudFront / ALB
   |
ECS Fargate - FastAPI
   |
   +---- RDS PostgreSQL
   +---- Redis (when required)
   +---- S3
   +---- Secrets Manager
   +---- CloudWatch
```

Use ECR for container images.

Do not introduce EKS or a distributed microservice topology for MVP.

## 5. Backend Module Boundaries

```text
app/
  api/            HTTP routes and dependency wiring
  core/           configuration, security, common utilities
  db/             database session and migrations integration
  models/         persistence models
  schemas/        Pydantic request/response contracts
  services/       business services
  methodology/   methodology and factor resolution
  providers/     provider adapters and registry integration
```

Controllers/routes must remain thin. Business logic belongs in services.

## 6. Estimation Pipeline

```text
AIWorkload
  |
Validate
  |
Resolve Provider
  |
Resolve Model
  |
Resolve Methodology
  |
Resolve Factors
  |
Energy Estimate
  |
Water Estimate
  |
Carbon Estimate
  |
Uncertainty Propagation
  |
Confidence
  |
Estimate
```

Each stage must be independently testable.

## 7. Provider Adapter Pattern

Provider-specific metadata normalization belongs in adapters.

```text
ProviderAdapter
  +-- OpenAIAdapter
  +-- AnthropicAdapter
  +-- GoogleAdapter
  +-- Future adapters
```

Adapters map provider-specific request telemetry to the canonical AIWorkload representation.

The Footprint Engine must not contain provider-specific branching where avoidable.

## 8. Methodology Layer

Methodology is data-driven and versioned.

```text
MethodologyVersion
    |
    +-- Factors
    +-- Assumptions
    +-- Sources
    +-- Limitations
```

Environmental coefficients must not be hard-coded directly into Python application logic.

## 9. Data Flow

### Developer SDK

```text
Developer Application
   |
SDK / Middleware
   |
AI provider request metadata
   |
AI Footprint API
   |
AIWorkload
   |
Estimate
   |
Developer Application / Dashboard
```

### Consumer

```text
User activity
   |
Manual / Share / Future integration
   |
AIWorkload
   |
Footprint API
   |
Estimate
   |
Mobile/Web UI
```

## 10. Multi-Tenancy

Hierarchy:

```text
Organization
   |
   +-- Project
        |
        +-- API Keys
        +-- Workloads
        +-- Estimates
```

All tenant-owned data must be scoped by organization.

## 11. Security Boundary

```text
Client
  |
HTTPS
  |
API Authentication
  |
Authorization
  |
Tenant-scoped service layer
  |
Database
```

API keys are secrets and must be hashed at rest.

## 12. Storage Strategy

### PostgreSQL
Primary system of record for:

- users/organizations
- projects
- API keys (hashed)
- workloads
- estimates
- providers
- models
- methodology metadata
- factor metadata
- audit events

### S3
Use for larger methodology/source artifacts or future reports. Do not use S3 as the primary transactional database.

### Redis
Use only when needed for:

- rate limiting
- caching
- short-lived distributed state

## 13. API Contract Principle

API responses must be stable and versioned.

External API path:

`/v1/...`

Breaking changes require a new API version.

## 14. Estimate Contract

An estimate contains:

- metric ranges
- units
- confidence
- evidence level
- methodology version
- assumptions

An estimate may explicitly contain `insufficient_data` for a metric.

## 15. Immutability Rules

Methodology versions are immutable once published.

Historical estimates keep the methodology version with which they were created.

API usage records should remain auditable.

## 16. Coding and Agentic Architecture

Composite workloads use parent/child relationships.

```text
CodingAgentSession
   |
   +-- LLM inference
   +-- LLM inference
   +-- tool metadata
   +-- LLM inference
```

Child events can reference `parent_workload_id`.

Aggregate estimates operate on supported child events.

## 17. Extensibility Requirements

Adding a provider must require:

1. provider registration
2. provider/model metadata
3. adapter implementation if ingestion is required
4. methodology factors/data
5. tests

It must not require rewriting the core Footprint Engine.

Adding a modality must similarly be localized to workload schemas, factors and estimator logic.

## 18. Failure Strategy

If a workload is unsupported or lacks sufficient methodology evidence:

- preserve the workload event if valid
- return an explicit unavailable status for the affected metric
- do not fabricate values

## 19. Observability

Every API request should have a request ID.

Monitor:

- request volume
- latency
- error rate
- estimate failures
- authentication failures
- database health

## 20. Environment Strategy

Maintain:

- development
- staging
- production

Each environment uses separate configuration and secrets.

## 21. CI/CD

GitHub Actions should perform:

1. formatting/linting
2. type/static checks where applicable
3. unit tests
4. integration tests
5. security/dependency checks
6. Docker build
7. deployment to staging

Production deployment should require explicit approval during MVP.

## 22. Architectural Non-Goals

MVP does not require:

- Kubernetes
- microservice-per-provider architecture
- event streaming platform
- real-time data-center telemetry
- direct interception of private consumer app traffic
- storing user prompts as a core requirement

## 23. Key Architectural Decisions

### ADR-001: AIWorkload as core abstraction
Chosen to support multimodal and agentic AI.

### ADR-002: Data-driven methodology
Chosen to allow scientific updates without changing application code.

### ADR-003: Ranges instead of false precision
Chosen to represent uncertainty honestly.

### ADR-004: Provider adapters
Chosen to isolate provider-specific interfaces from the core engine.

### ADR-005: Modular monolith for MVP
Chosen to maximize development speed while preserving future decomposition boundaries.

### ADR-006: Static/versioned benchmark definitions instead of a database table
Benchmark definitions describe fixed workload shapes, not environmental data, and change rarely. A static, versioned Python module reuses the existing taxonomy directly, requires no migration, and avoids building CRUD/admin surface for a small, curated set of definitions. A database-backed registry can be introduced later if benchmarks need to be managed without a deploy.

### ADR-007: Comparison and benchmark execution are stateless
Neither reads nor writes tenant-owned data, so neither can regress organization/project isolation. Results are computed on demand from the same registries `/v1/estimate` already reads. Persistence is deferred until a concrete requirement (e.g. historical comparison tracking) is demonstrated, per the "prefer stateless execution" principle.

### ADR-008: Comparison candidates are never ranked
Declaring a provider/model "best," "cheapest," or "recommended" would assert a value judgment and a precision the methodology does not support, and would conflict with provider neutrality. The API exposes comparable measurements only; the schema itself carries no ranking/score field, structurally preventing this rather than relying on a convention.

### ADR-009: Methodology data is never fabricated
No production environmental factor is added without an authoritative source, documented provenance, an assigned methodology version, an evidence level and explicit approval. Absent that, the pipeline returns `insufficient_data`. This applies identically to comparison, benchmarking and normalization - none of them are permitted to invent a coefficient merely to produce a non-empty response.

### ADR-010: Normalization denominators are explicit and workload-derived
Per-token, per-image, per-second and per-minute denominators are computed from the requested workload's own populated quantity fields, never inferred or defaulted for a workload type that lacks the relevant field. The basis (e.g. `input_plus_output`) is always returned alongside the normalized value so the calculation is auditable rather than implicit.

### ADR-011: Methodology validation is separate from runtime estimation
`scripts/validate_methodology.py` is read-only, advisory tooling for data governance (referential integrity, ranges, provenance completeness, TEST_ONLY-vs-production classification). It never runs at request time, never alters data, and never re-implements factor resolution - `EstimationPipeline`/`FactorRepository` remain the sole runtime authority, so there is exactly one estimation path.

### ADR-013: Client/integration metadata is a JSON column on the existing workload row, not a new table
Sprint 6's client/integration metadata (`client_type`, `client_name`, `client_version`, `integration_type`, `integration_version`, `runtime`) is small, fully optional, changes independently of any other workload field, and needs to be queryable for future client-adoption analytics without needing its own lifecycle or CRUD surface - the same reasoning ADR-006 applies to benchmark definitions. It is stored as a single nullable `client_context` JSON column on `ai_workloads` (one additive, backward-compatible migration) rather than a new table or individual columns per field, and is represented on the wire as the typed, versioned `ClientContext` Pydantic model (not the pre-existing free-form `metadata` field) so it gets real OpenAPI enum/type documentation. It is never read by `WorkloadValidator` or `EstimationPipeline`, so it structurally cannot affect an estimate, and it carries no organization/project/application fields, so it structurally cannot be mistaken for authorization data.

## 24. Future Decomposition

Only after scale requires it, services may be separated into:

- API service
- workload ingestion service
- estimation service
- methodology service
- analytics service
- billing service

The v0.1 architecture should not prematurely implement these as separate deployable services.
