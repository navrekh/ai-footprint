# AI FOOTPRINT
## Product Requirements Document (PRD)
### Version 0.3 — Foundation + Developer Platform + Resource Intelligence + Developer Experience

**Product:** AI Footprint  
**Working tagline:** Know the hidden resource impact of AI.  
**Status:** Approved — Sprint 5 baseline  

## 1. Executive Summary

AI Footprint is a provider-neutral technology platform designed to make the estimated physical resource impact of artificial intelligence understandable to users and measurable for developers and organizations.

AI usage spans conversational AI, image generation, video generation, audio, coding assistants, code review, AI agents, RAG, embeddings and other workloads. Users generally see the output of AI but not the infrastructure and resource implications associated with producing it.

AI Footprint exposes estimated:

- Water consumption / water footprint
- Energy consumption
- Carbon emissions
- Compute/resource intensity

The platform shall not claim to measure exact physical resource consumption of an individual request unless authoritative measurement data is available. Estimates shall be presented with ranges, confidence, methodology version, assumptions and source provenance.

The platform is designed around an **AIWorkload** abstraction and a hierarchical developer model:

```text
Organization
  └── Project
       └── Application
            ├── API Keys
            └── AI Workloads
                 └── Estimates
```

An Organization is the tenant/security boundary. A Project is the operational and future billing boundary. An Application represents a specific AI product, service, environment or client workload within a Project.

## 2. Product Vision

Make the resource impact of AI visible, understandable and measurable without requiring users to understand data-center infrastructure.

For developers and organizations, AI Footprint should become a resource-intelligence layer that answers:

- How much AI workload are we running?
- What estimated energy, water and carbon impact does that workload represent?
- Which providers, models, activities and applications contribute to that impact?
- How much of our workload is actually measurable with available methodology data?
- How confident should we be in the reported estimates?

## 3. Target Users

### Consumer
People using AI applications who want to understand their AI resource footprint.

### AI Developer
Developers building AI-powered applications who want to expose resource impact to users.

### Engineering Teams
Organizations using AI coding assistants, coding agents and automated AI workflows.

### Enterprise
Organizations wanting aggregate AI resource intelligence across applications and projects.

### AI Platforms / Providers
AI companies wanting to provide resource transparency within their products.

## 4. Product Principles

1. Transparency
2. Scientific humility
3. Privacy first
4. Provider neutral
5. AI-workload centric
6. Human understandable
7. Developer friendly
8. Methodology versioning
9. Reproducibility
10. Measurement coverage must be explicit

## 5. Core Product Abstraction

The fundamental object is **AIWorkload**, not AIPrompt.

This supports multimodal, infrastructure and agentic workloads without requiring the platform to store private AI content.

## 6. Domain Hierarchy

### Organization
Top-level tenant and security boundary.

### Project
Operational boundary within an organization. Projects are the primary boundary for API-key scope, usage aggregation and future billing.

### Application
A specific AI product, service, environment or workload source within a project. Examples include Customer Support AI, Internal Copilot and Coding Agent.

An Application has:

- name
- slug
- description
- status
- optional environment: development, staging or production
- project ownership
- created/updated timestamps

### API Key
Authentication credential used to access protected APIs. API keys remain organization-level or project-scoped in the initial platform; application-scoped keys are deferred until a concrete security requirement exists.

### AIWorkload
The measurable unit of AI activity. A workload may represent an inference, generation, embedding operation, tool-driven step, media operation, coding task or aggregate session.

### Estimate
The resource-impact result associated with a workload, including range, confidence, methodology and provenance.

## 7. AI Workload Taxonomy

### Conversational AI
- Text generation
- Reasoning
- Research
- Summarization
- Classification

### Image AI
- Image generation
- Image editing
- Image enhancement
- Image upscaling
- Vision processing

### Video AI
- Text-to-video
- Image-to-video
- Video editing
- Video enhancement

### Audio AI
- Speech-to-text
- Text-to-speech
- Audio generation

### Coding AI
- Code generation
- Code explanation
- Debugging
- Refactoring
- Test generation
- Code review
- Repository analysis

### Agentic AI
- Tool calls
- Browser agents
- Coding agents
- Multi-step autonomous workflows

### AI Infrastructure
- Embeddings
- RAG
- Batch inference
- Classification
- Extraction
- Fine-tuning

## 8. MVP and Current Platform Scope

The initial MVP establishes the measurement infrastructure. Sprint 1 and Sprint 2 establish the backend foundation, persistence and lifecycle management. Sprint 3 extends this into a developer platform and usage-intelligence layer. Sprint 4 extends this into cross-provider AI resource intelligence (workload comparison, standardized benchmarks and normalized resource intensity). Sprint 5 extends this into developer experience and productization (documentation, Quick Start, official Python SDK and a developer console), without adding new estimation capability.

### Foundation
- Footprint Engine
- Provider registry
- Model registry
- Workload taxonomy
- Estimation API
- Methodology API
- Authentication
- API key lifecycle
- Workload and estimate persistence
- Idempotent event ingestion
- Audit-ready request metadata

### Developer Platform
- Organization management
- Project management
- Application management
- Application-aware workloads
- Usage summaries
- Usage breakdown by provider
- Usage breakdown by model
- Usage breakdown by activity
- Usage breakdown by application
- Usage time series
- Measurement coverage reporting

### AI Resource Intelligence
- Workload comparison across provider/model candidates
- Standardized, versioned benchmark definitions
- Benchmark listing, retrieval and execution
- Normalized resource intensity (per token/image/second/minute where defensible)
- Methodology-data governance and validation tooling

### Developer Experience & Productization
- Complete developer-facing API documentation and OpenAPI contract
- Quick Start enabling a first successful measurement in approximately 10 minutes
- Official thin Python SDK (REST client only, no estimation logic)
- Minimal developer console (dashboard, projects, applications, API keys, usage, compare)
- Interactive API Explorer
- Visible request correlation (request_id, workload_id, estimate_id)

### Initial Providers
- OpenAI
- Anthropic
- Google

### Initial Workloads
- Text
- Image
- Video
- Coding
- Infrastructure and agentic workload taxonomy as supported by methodology data

### Metrics
- Energy
- Water
- CO2e

### Estimate metadata
- Range
- Confidence
- Evidence level
- Methodology version
- Assumptions
- Source references

## 9. Usage Intelligence Requirements

Usage intelligence must be derived from persisted AIWorkload and Estimate records rather than maintaining a separate synchronized usage ledger in the initial implementation.

The platform shall support:

- total workloads
- measurable workloads
- partial/insufficient-data workloads
- energy ranges
- water ranges
- carbon ranges
- measurement coverage percentage
- breakdowns by provider, model, activity and application
- daily, weekly and monthly time series
- custom date-range aggregation

### Coverage semantics

Coverage must be explicit. For example, if 7,500 of 10,000 workloads have defensible methodology coverage, the platform reports 75% measurement coverage and must not present the aggregate as if all 10,000 workloads were fully measured.

Aggregations must preserve range semantics. Minimum and maximum values shall be aggregated without collapsing uncertainty into a false point estimate.

If an aggregate contains unsupported or insufficient-data workloads, the aggregate status shall communicate `partial` or `insufficient_data` as appropriate.

## 10. User Experience

### Consumer
Install/open → account → record activity → estimate → understand → history → share.

### Developer
Sign up → organization → project → application → API key → Quick Start → submit AI workload → receive estimate → view usage → compare workloads → integrate SDK.

### Enterprise
Organization → projects → applications → API integrations → aggregate usage → measurement coverage → analytics/reporting.

## 11. Business Model

Primary model: **free awareness → paid infrastructure**.

### Consumer
Free basic footprint and history. Optional future Pro for advanced analytics and exports.

### Developer API
Usage-based plans with free, startup, growth and enterprise tiers.

### Enterprise
Subscription based on workload volume, applications, users, analytics and integrations.

Billing implementation is not part of Sprint 1–5.

## 12. Privacy

Prefer metadata over content. Core measurement should not require storing prompts, generated responses, private images or source code.

Application, provider, model, workload metadata and measurement results should be stored only to the extent required for estimation, analytics, security, reproducibility and future billing.

## 13. Security and Tenant Isolation

- Organization is the tenant boundary.
- Project-scoped credentials may access only their project.
- Organization-level credentials may operate across projects according to endpoint rules.
- Application access must be constrained to the owning project and organization.
- Cross-tenant resources must not be disclosed.
- Single-record and collection endpoints must enforce the same project/application scope semantics.

## 14. Success Metrics

### Product
- Registered users
- Active users
- AI workloads measured
- Measurement coverage
- Repeat usage
- Weekly retention
- Shared reports

### Developer
- API signups
- API keys created
- Active projects
- Active applications
- Monthly workloads
- SDK adoption
- Usage dashboard engagement
- Quick Start completion rate
- API Explorer usage

### Business
- Free-to-paid conversion
- Recurring revenue
- API revenue
- Enterprise customers

## 15. Roadmap

### Phase 0 — Foundation
PRD, FRD, architecture, methodology, data model, API specification.

### Phase 1 — Footprint Engine
Calculation engine, provider/model registry, methodology registry, tests.

### Phase 2 — Developer Platform / Productization
Developer accounts, projects, API keys, application management, usage intelligence, resource intelligence, developer console, docs and SDKs, delivered across:

- Sprint 1 — Footprint Engine
- Sprint 2 — Persistence & Lifecycle
- Sprint 3 — Developer Platform & Usage Intelligence
- Sprint 4 — AI Resource Intelligence
- Sprint 5 — Developer Experience & Productization

### Phase 3 — Consumer Web/Mobile
Mobile UX, application, activity history, dashboard, shareable footprint.

### Phase 4 — Integrations
Browser extension, GitHub, coding tools, AI application SDK.

### Phase 5 — Enterprise
Advanced organization management, analytics, reporting, SSO, RBAC and gateway.

### Phase 6 — AI Resource Intelligence (continued)
Sprint 4 delivered the initial cross-provider comparison and standardized benchmarking foundation under Phase 2. This phase covers what remains beyond that: deeper cross-provider observability, agent-workload analytics, and optimization insights. This phase does not include a ranking, scoring or recommendation engine, which remain explicit non-goals.

## 16. Sprint 3 — Developer Platform & Usage Intelligence

Sprint 3 shall deliver the backend foundation for developer-facing usage intelligence.

### In scope
1. Application entity and database migration
2. Application CRUD
3. Application/project/organization isolation
4. `application_id` association on AI workloads
5. Validation that an application belongs to the workload's project
6. Usage summary API
7. Usage by provider API
8. Usage by model API
9. Usage by activity API
10. Usage by application API
11. Usage time-series API
12. Measurement coverage metrics
13. Range-aware aggregation
14. Filtering by project/application/date range where applicable
15. Pagination or bounded result sets for high-cardinality breakdowns
16. Tests for authorization, aggregation and incomplete-data semantics
17. OpenAPI documentation

### Suggested endpoints

- `POST /v1/applications`
- `GET /v1/applications`
- `GET /v1/applications/{application_id}`
- `PATCH /v1/applications/{application_id}`
- `GET /v1/usage/summary`
- `GET /v1/usage/by-provider`
- `GET /v1/usage/by-model`
- `GET /v1/usage/by-activity`
- `GET /v1/usage/by-application`
- `GET /v1/usage/timeseries`

Usage APIs should accept explicit date ranges and use PostgreSQL aggregation initially.

### Out of scope for Sprint 3

- Frontend/dashboard UI
- SDK implementation
- Live provider integrations
- Billing and payments
- RBAC/SSO
- AWS production deployment
- Redis/Kafka
- Data warehouse
- Materialized usage tables
- Consumer mobile application
- Application-scoped API keys

## 17. Sprint 4 — AI Resource Intelligence

The product-level capability introduced in Sprint 4 is **AI Resource Intelligence**: provider-neutral understanding and comparison of the resource intensity of AI workloads. Comparison and benchmarking are features of that capability, not the capability itself.

This evolves the platform's framing from "an AI workload footprint estimation API" toward "provider-neutral AI resource intelligence for understanding and comparing the resource intensity of AI workloads," while every existing product principle (provider neutrality, workload-centricity, methodology-driven estimation, range-based uncertainty, confidence-awareness, no fabricated factors, no false precision) remains mandatory and unchanged.

### In scope

1. Workload comparison across multiple provider/model candidates for one workload definition (`POST /v1/compare`).
2. Standardized, deterministic, versioned benchmark definitions aligned to the existing workload taxonomy (`GET /v1/benchmarks`, `GET /v1/benchmarks/{id}`, `POST /v1/benchmarks/run`).
3. Normalized resource intensity (e.g. per 1K tokens, per image, per second, per minute) as presentation-layer arithmetic over an existing approved estimate, with explicit, auditable denominator semantics.
4. A methodology-data governance and validation mechanism so the platform can safely accept authoritative methodology data in the future, without weakening the "never fabricate" principle now.

### Comparison semantics

Comparison evaluates one workload definition against multiple provider/model candidates. Each candidate is estimated **independently** through the existing estimation engine. Every candidate retains its own range, status, confidence, evidence level, accounting boundary, methodology version, assumptions and provenance. Candidates are never aggregated, averaged, or collapsed into a single figure, and the API never declares a candidate a winner, loser, "best," "cheapest," or "recommended" model. The API provides comparable measurements; the caller makes the decision.

### Benchmark semantics

A benchmark is a deterministic, versioned, named workload definition expressed entirely in terms of the existing workload taxonomy (activity type, modality, and the same optional quantity fields used elsewhere). Benchmark execution reuses the same estimation and comparison mechanism as ad hoc comparison — it does not introduce a second estimation path. A benchmark may legitimately return `insufficient_data` when no approved methodology factor exists; this is expected, correct behavior, not a defect to work around by inventing a coefficient.

### Normalization semantics

Where a scientifically defensible denominator exists for a workload's populated quantity fields (tokens for text, image count for image, seconds for video, minutes for audio), the platform may expose a normalized resource-intensity range alongside the raw range. Token normalization is never forced onto non-token workloads, and no denominator is invented for a workload type that lacks one. Every normalized value preserves the underlying estimate's status, confidence, methodology version, and provenance, and is itself expressed as a min/max range — never averaged into a single point value.

### Methodology governance

Sprint 4 does not add real provider/model environmental factors. Production methodology data continues to require an authoritative source, documented provenance, an assigned methodology version, an evidence level, and explicit production approval before it is used at runtime. Where that data does not yet exist, the platform continues to report `insufficient_data` rather than a fabricated or internet-sourced estimate. A read-only validation tool checks methodology data for structural completeness and correctly distinguishes production-approved data from `TEST_ONLY` fixture data, but this tool is advisory — it does not grant approval and does not alter runtime behavior.

### Security model

`POST /v1/compare` and `POST /v1/benchmarks/run` require a valid API key but perform no tenant-scoped reads or writes: nothing organization- or project-owned is read, written, or returned. `GET /v1/benchmarks` and `GET /v1/benchmarks/{id}` are public reference-data endpoints, consistent with the existing provider/model/methodology registries. No change is made to organization isolation, project isolation, or API-key scope enforcement established in Sprint 2/3.

### Explicit non-goals for Sprint 4

- No ranking, scoring, or recommendation engine of any kind.
- No persistent comparison or benchmark-result storage.
- No frontend, dashboard, mobile application, SDKs, or live provider API integrations.
- No billing, Stripe, RBAC/SSO, AWS deployment, Redis, Kafka, or data warehouse.
- No fabricated or internet-sourced production environmental factors for any provider.

## 18. Sprint 5 — Developer Experience & Productization

The product objective of Sprint 5 is to make AI Footprint usable by an external developer without requiring knowledge of the internal repository or estimation-engine implementation. The primary Sprint 5 outcome is developer usability, not additional estimation capability.

**Implementation status:** Sprint 5 was delivered in sub-phases. Sprint 5A (developer API productization: OpenAPI/reference documentation, request correlation, CORS), Sprint 5B (the official Python SDK, described below), Sprint 5C (the developer console foundation: Dashboard, Projects, Applications, API Keys, session/auth architecture per ADR-012), and Sprint 5D (Usage, Compare, Benchmarks, and the API Explorer within that console) are implemented. Only the in-console Documentation section described later in this section remains a specification for a future sub-phase.

Target developer journey:

Sign up → Create Organization → Create Project → Create Application → Create API Key → Read Quick Start → Send first workload → Receive footprint → View usage → Compare workloads → Integrate SDK.

### In scope

1. Developer API productization: a clear, stable, well-documented developer-facing API contract over the existing endpoints.
2. Complete OpenAPI and reference documentation: authentication, API key usage, request/response examples, error contract, request IDs, idempotency, pagination, date ranges, insufficient-data semantics, methodology/provenance, and privacy behavior.
3. Quick Start: a developer unfamiliar with the repository should be able to make a first successful measurement in approximately 10 minutes.
4. A thin official Python SDK that calls the REST API and does not duplicate footprint-estimation logic.
5. A minimal developer console: dashboard, projects, applications, API keys, usage, compare, API Explorer, and documentation.
6. An interactive API Explorer for constructing, executing and inspecting authenticated API calls, including request_id visibility and error explanation.
7. A usage overview UI that visualizes the existing usage APIs.
8. A compare/benchmark UI that exposes the existing Sprint 4 capabilities.
9. Integration diagnostics: visible request correlation (request_id, workload_id, and estimate_id where available) to help developers troubleshoot integrations.

### Developer API productization

Existing capabilities must be documented clearly, without changing endpoint behavior:

- `POST /v1/estimate` — stateless calculation, not persisted.
- `POST /v1/events` — workload ingestion and persistence, with an associated estimate created when supported.
- `POST /v1/batch-estimate` — bounded, stateless batch calculation.
- `POST /v1/compare` — provider/model comparison for one workload definition.
- `GET /v1/benchmarks`, `GET /v1/benchmarks/{id}`, `POST /v1/benchmarks/run` — standardized benchmark definitions and execution.
- `GET /v1/usage/summary`, `GET /v1/usage/by-provider`, `GET /v1/usage/by-model`, `GET /v1/usage/by-activity`, `GET /v1/usage/by-application`, `GET /v1/usage/timeseries` — usage intelligence.

`POST /v1/estimate` and `POST /v1/events` must be explicitly distinguished in all developer-facing documentation: the former is stateless calculation with no persistence; the latter is workload ingestion/persistence, with an associated estimate created when supported.

### Python SDK

**Delivered in Sprint 5B** (`sdk/`, package name `aifootprint`, Python `>=3.10`). Actual interface:

```python
from aifootprint import AIClient

client = AIClient(api_key="afp_live_xxx")

result = client.events.create(
    project_id="proj_xxx",
    application_id="app_xxx",
    provider="openai",
    model="model-id",
    modality="text",
    activity_type="text_generation",
    input_tokens=2000,
    output_tokens=1000,
)
```

The client class is named `AIClient` rather than the `AI` used in this section's original conceptual sketch, for clarity at call sites. The delivered SDK exposes one namespace per resource — `organizations`, `projects`, `applications`, `api_keys`, `estimates`, `events`, `batch`, `workloads`, `usage`, `compare`, `benchmarks`, `providers`, `models`, and `methodology` — a superset of the original sketch's `events`/`estimates`/`usage`/`compare`/`benchmarks`, since onboarding (organizations/projects/applications/API keys) and the public registries turned out to be necessary for a developer to use the SDK without any raw HTTP calls at all. It contains no estimation logic, environmental coefficients, or duplicate methodology calculation — it is a client of the existing REST API, nothing more. See `sdk/README.md` for its Quick Start.

### Developer console and API Explorer

**Delivered across Sprint 5C and Sprint 5D.** A minimal developer console (Dashboard, Projects, Applications, API Keys — Sprint 5C; Usage, Compare, Benchmarks, API Explorer — Sprint 5D; Documentation remains a placeholder) prioritizing developer onboarding and API usability over enterprise analytics. The delivered API Explorer authenticates through the console's existing session (no separate key entry) and derives its endpoint list from the backend's own `GET /openapi.json` rather than a hand-maintained duplicate, executing every request through the same client every other page uses; a developer chooses an endpoint, supplies path/query parameters and a request body where applicable, executes it, and inspects the formatted response, HTTP status, request ID, and any errors.

The delivered usage overview and compare/benchmark UI preserve measurement coverage, min/max ranges, confidence, and insufficient-data states exactly as the underlying APIs report them, and never convert a range into a false point estimate. The compare/benchmark UI introduces no winner, best model, score, ranking, or recommendation — it presents measurements and methodology information only, with the Compare and Benchmarks result views sharing one rendering component specifically so this guarantee cannot silently diverge between the two.

### Privacy and idempotency

The developer integration must not require prompts, generated responses, private images, or source code — core measurement continues to operate on workload metadata only. The SDK provides a convenient, first-class mechanism for supplying an idempotency key for event ingestion, documenting the existing idempotency contract rather than redesigning it.

### No new estimation logic

Sprint 5 must not introduce another estimation path, estimation algorithm, environmental coefficient, methodology calculation, or provider-specific calculation logic. Sprint 4's estimation engine remains the single runtime authority.

### Explicit non-goals for Sprint 5

- Live provider interception; automatic OpenAI, Anthropic, or Google integration.
- Browser extension, GitHub App, or mobile application.
- Billing, Stripe, RBAC, or SSO.
- Kafka; Redis unless later justified by an actual requirement; data warehouse; Kubernetes; enterprise gateway.
- Optimization engine or recommendation engine.
- New footprint calculation logic, new environmental coefficients, or a new methodology estimation path.

## 19. Out of MVP / Deferred

The following do not block the developer-platform MVP:

- iOS deep integration
- Android system-wide monitoring
- every LLM integration
- automatic interception of private AI conversations
- enterprise gateway
- GitHub App
- browser extension
- automated billing
- ESG certification
- real-time data-center telemetry
- full analytics warehouse

## 20. MVP Release Criteria

1. Developer registration works.
2. API keys can be created and revoked.
3. Supported workloads can be submitted.
4. The system returns an estimate or insufficient-data status.
5. Every estimate includes range, confidence and methodology version.
6. Estimates are reproducible.
7. Provider/model data is versioned.
8. Workload usage is persisted.
9. Applications can be created and associated with workloads.
10. Usage can be queried by project and application.
11. Aggregate usage preserves range and data-coverage semantics.
12. Developer console can consume usage APIs (Sprint 5).
13. Automated tests pass.
14. API documentation is available.
15. Privacy behavior is documented.
16. No unsupported precision claims are made.
17. New providers can be added without modifying the core estimation architecture.
