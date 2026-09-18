# AI FOOTPRINT
## Product Requirements Document (PRD)
### Version 0.5 — Foundation + Developer Platform + Resource Intelligence + Developer Experience + Adoption & Instrumentation + CLI

**Product:** AI Footprint  
**Working tagline:** Know the hidden resource impact of AI.  
**Status:** Approved — Sprint 7 specification  

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

## 38. Sprint 6 — Adoption & Instrumentation Foundation

### 38.1 Objective

Sprint 6 establishes the common adoption and instrumentation layer that allows AI Footprint to be consumed consistently by multiple client surfaces without duplicating workload measurement or estimation logic.

The strategic objective is:

> Create a unified instrumentation contract through which the Web Console, SDKs, CLI, Browser Extension, Mobile applications and direct API integrations can identify and submit AI workloads using one canonical AI Footprint model.

Sprint 6 is a platform-foundation sprint. It does not attempt to build the complete CLI, Browser Extension or Mobile applications. Those clients are subsequent delivery surfaces that must consume the contracts established here.

### 38.2 Product evolution

The product evolves from a developer-facing API and console into a multi-surface AI resource intelligence platform:

~~~text
                         AI Footprint Platform
                                  |
                         AIWorkload Contract
                                  |
                    +-------------+-------------+
                    |                           |
              Estimation /                Usage /
              Provenance                  Intelligence
                    |                           |
       +------------+------------+--------------+------------+
       |            |            |              |            |
      Web          SDK          CLI        Browser Ext.   Mobile
    Console                     (S7)          (S8)        (S9)
~~~

The API remains the system-of-record interface for external clients. Client applications must not implement independent footprint calculations.

### 38.3 In scope

1. Define a canonical client/integration metadata contract.
2. Define how an AIWorkload identifies its originating client surface.
3. Extend workload/event contracts only where required to carry client/integration metadata.
4. Establish a stable instrumentation contract for future SDK, CLI, Browser Extension and Mobile clients.
5. Define privacy-preserving instrumentation rules.
6. Establish client/integration taxonomy and version semantics.
7. Define event-ingestion behavior for instrumented workloads.
8. Define compatibility rules for future client versions.
9. Add API/OpenAPI documentation for the instrumentation contract.
10. Add backend validation and regression tests.
11. Add SDK model/client support only where required to represent the new contract; do not add estimation logic.
12. Document the extension/mobile/CLI integration boundaries for subsequent sprints.
13. Preserve all existing authentication, authorization, tenant isolation, idempotency, provenance, range and uncertainty semantics.

### 38.4 Canonical client metadata

The platform shall distinguish Application identity from Client/Integration identity.

Application answers: Which AI product, service, environment or workload source does this workload belong to?

Client/Integration metadata answers: Through which software surface or integration was this workload instrumented?

These concepts must not be conflated.

The client contract should support, at minimum:

- client type
- client name
- client version
- integration type
- optional integration version
- optional non-sensitive runtime metadata

The exact wire representation shall be defined in the Sprint 6 FRD and OpenAPI contract rather than allowing each client to invent fields.

### 38.5 Initial client taxonomy

The platform should support the following client categories as controlled values or an explicitly versioned extensible taxonomy:

- web
- python_sdk
- javascript_sdk
- cli
- browser_extension
- ios
- android
- direct_api

This taxonomy describes the instrumentation surface, not the AI provider.

New client types must not require changes to the estimation engine.

### 38.6 AIWorkload remains the canonical abstraction

Sprint 6 does not replace AIWorkload with Prompt, Session, Interaction or ClientEvent.

The workload continues to represent the measurable unit of AI activity and retains:

- provider
- model
- model version
- modality
- activity type
- workload quantities
- timestamp
- project/application association where applicable
- parent workload relationship where applicable
- metadata
- estimate/provenance

Client metadata is additive context about the origin of the workload.

### 38.7 Privacy requirements

Instrumentation must be privacy-first.

The default contract must not require:

- prompt content
- model response content
- private images
- audio content
- video content
- source code
- browser page contents
- cookies
- authentication tokens belonging to third-party AI services

Client implementations should prefer measurable metadata such as:

- provider/model identifiers
- workload type
- token or media quantities when available
- duration
- application/integration identifier
- client type/version
- timestamp
- user-controlled metadata

The Browser Extension must eventually be capable of operating without transmitting private AI conversation content to AI Footprint.

### 38.8 Instrumentation semantics

A client reports an AI workload to AI Footprint; it does not report an environmental estimate unless the API contract explicitly supports an externally supplied, provenance-qualified measurement in a future release.

The canonical flow is:

~~~text
AI activity
   |
Client instrumentation
   |
Canonical AIWorkload metadata
   |
POST /v1/events
   |
Existing validation / resolver / estimation pipeline
   |
Estimate
   |
Persisted workload + estimate
   |
Usage / Console / future client surfaces
~~~

The measurement engine remains the sole runtime authority for AI Footprint-generated estimates.

### 38.9 Idempotency and replay

Instrumented clients must use the existing idempotency contract where an event may be retried.

The client layer must not invent a second deduplication mechanism.

Repeated submission of the same client-supplied idempotency key within the applicable project scope continues to return the original workload/estimate according to the existing Sprint 2 semantics.

### 38.10 Client versioning

Client metadata must support independent client versioning.

A new Browser Extension version, SDK release or CLI release must not imply a new AI Footprint API version.

Breaking changes to the external API continue to require a new API version.

Client metadata is observational/instrumentation metadata and must not alter estimation behavior unless a future explicitly approved methodology requires it.

### 38.11 SDK direction

The existing Python SDK remains a thin REST client.

Sprint 6 may add typed support for the new instrumentation metadata contract if required by the API. It must not add footprint calculation, provider-specific environmental logic or local estimation.

Future SDKs must follow the same contract.

### 38.12 CLI direction

Sprint 6 defines the CLI integration contract but does not deliver the full CLI product.

Sprint 7 will use this contract to provide developer workflow commands such as event submission and usage inspection.

The CLI must remain a client of the API.

### 38.13 Browser Extension direction

Sprint 6 defines the privacy and instrumentation boundary for the future Browser Extension.

The extension will eventually be an awareness and measurement surface for supported AI web applications.

The extension must:

- minimize data collection
- avoid collecting conversation content by default
- use explicit site-level/user-level controls
- send only the metadata necessary for workload identification and measurement
- use the AI Footprint API rather than implementing independent environmental calculations

Extension UI and site-specific adapters are Sprint 8 scope, not Sprint 6 scope.

### 38.14 Mobile direction

Sprint 6 defines the API/client boundary for future iOS and Android clients.

Mobile applications will eventually provide personal AI resource awareness, history and related experiences.

Mobile applications must consume the same workload, estimate, usage and methodology contracts as other clients.

Native mobile UI, distribution and mobile-specific telemetry are deferred.

### 38.15 Success criteria

Sprint 6 succeeds when:

1. A canonical client/integration metadata contract exists.
2. The contract is represented in OpenAPI.
3. Existing event ingestion remains backward compatible.
4. Instrumented workloads can identify their originating client surface.
5. Application identity remains distinct from client identity.
6. Privacy requirements are explicit and testable.
7. Existing idempotency semantics remain unchanged.
8. Client versioning is independent of API versioning.
9. The Python SDK can represent the instrumentation contract where applicable.
10. No client contains independent estimation logic.
11. Future CLI, Browser Extension and Mobile clients can consume the same API contract.
12. Existing Sprint 1–5 functionality remains backward compatible.
13. Automated tests and static checks pass.

### 38.16 Explicit non-goals

Sprint 6 does not include:

- full CLI implementation
- Browser Extension implementation
- Chrome Web Store or Firefox Marketplace distribution
- iOS application
- Android application
- App Store or Play Store distribution
- JavaScript SDK implementation beyond contract planning
- direct interception of private AI traffic
- provider credential capture
- prompt/response storage
- browser content storage
- new provider integrations
- new environmental coefficients
- new estimation algorithms
- optimization engine
- model routing
- rankings
- scoring
- recommendation engine
- billing
- payments
- RBAC
- SSO
- enterprise gateway
- Redis
- Kafka
- data warehouse
- Kubernetes
- persistent benchmark result storage

### 38.17 Sprint 6 delivery sequence

Recommended implementation sequence:

1. Freeze Sprint 5 baseline.
2. Define client/integration domain semantics.
3. Define canonical instrumentation schema.
4. Define OpenAPI request/response changes.
5. Implement backend validation and persistence changes only where necessary.
6. Update Python SDK types/resources only where required.
7. Add privacy/security/idempotency regression tests.
8. Validate backward compatibility with existing clients.
9. Document CLI, Browser Extension and Mobile integration contracts.
10. Review and merge Sprint 6 only after the complete verification gate passes.

### 38.18 Roadmap after Sprint 6

~~~text
Sprint 6  — Adoption & Instrumentation Foundation
Sprint 7  — CLI + Developer Workflow
Sprint 8  — Browser Extension
Sprint 9  — Mobile Apps
Sprint 10+ — Integrations / Enterprise / broader adoption
~~~

The platform must continue to expose one common AIWorkload and estimation foundation across every surface.


## 39. Sprint 7 — CLI + Developer Workflow

### 39.1 Objective

Sprint 7 delivers the first command-line developer surface for AI Footprint. The CLI must make AI Footprint usable from terminals, local development environments and CI/CD workflows while remaining a thin client of the existing Python SDK and REST API.

The strategic objective is:

> Make AI Footprint measurable from the developer workflow itself, without creating a second instrumentation, authentication or estimation architecture.

The CLI is an adoption surface, not a new measurement engine.

### 39.2 Product evolution

Sprint 7 extends the common Sprint 6 instrumentation foundation:

~~~text
Developer
   |
   v
AI Footprint CLI
   |
   v
Python SDK
   |
   v
AI Footprint REST API
   |
   +--> AIWorkload
   +--> Estimation Pipeline
   +--> Usage Intelligence
   +--> Resource Intelligence
~~~

The CLI must use the Sprint 6 `client_type=cli` client context and the existing canonical AIWorkload contract.

### 39.3 Target users

- AI developers
- software engineers
- platform/DevOps engineers
- engineering teams using AI coding tools or agents
- CI/CD and automation workflows
- developers evaluating AI workload resource impact

### 39.4 In scope

1. Installable `aifootprint` CLI package.
2. Top-level help and version commands.
3. `aifootprint event` for persisted workload submission.
4. `aifootprint estimate` for stateless workload estimation.
5. `aifootprint usage` for usage intelligence inspection.
6. `aifootprint compare` for existing provider/model comparison.
7. `aifootprint benchmarks` for existing benchmark discovery and execution.
8. API-key configuration through environment variables and a local developer configuration mechanism.
9. Configurable API base URL.
10. Human-readable terminal output.
11. Machine-readable JSON output.
12. Request ID visibility where returned by the SDK/API.
13. Consistent CLI exit codes for success, validation, authentication/authorization, not-found, rate-limit and server/transport failures.
14. Idempotency-key support for event ingestion.
15. Automatic CLI client metadata using the Sprint 6 contract.
16. CI/CD-friendly non-interactive operation.
17. Documentation and examples for local development and automation.
18. CLI unit/contract tests and packaging validation.

### 39.5 Explicit command contract

The initial command surface is:

~~~text
aifootprint --help
aifootprint --version

aifootprint event
aifootprint estimate
aifootprint usage
aifootprint compare
aifootprint benchmarks
~~~

Command names and flags must remain stable once published unless a documented breaking CLI change is required.

### 39.6 Event command

`aifootprint event` submits a canonical workload to `POST /v1/events`.

It must support the existing workload dimensions required by the backend, including:

- provider
- model
- optional model version
- modality
- activity type
- input/output tokens where applicable
- input/output characters where applicable
- image dimensions/count where applicable
- video duration/resolution where applicable
- audio duration where applicable
- tool calls
- duration
- project
- application
- metadata where supported
- idempotency key

The CLI automatically supplies client metadata equivalent to:

~~~json
{
  "client_type": "cli",
  "client_name": "aifootprint-cli",
  "client_version": "<installed-version>",
  "runtime": "<non-sensitive-runtime>"
}
~~~

The CLI must not require or capture prompt/response content.

### 39.7 Estimate command

`aifootprint estimate` calls the existing stateless `POST /v1/estimate` endpoint.

It must never perform footprint calculations locally.

The command must preserve:

- min/max ranges
- metric status
- confidence
- evidence level
- accounting boundary
- methodology version
- assumptions

### 39.8 Usage command

`aifootprint usage` consumes the existing usage APIs.

Initial capabilities should include:

~~~text
aifootprint usage summary
aifootprint usage by-provider
aifootprint usage by-model
aifootprint usage by-activity
aifootprint usage by-application
aifootprint usage timeseries
~~~

The CLI must preserve coverage and range semantics and must not replace ranges with averages or point estimates.

Date-range and applicable project/application/provider/model/activity filters must map directly to existing API parameters.

### 39.9 Compare command

`aifootprint compare` calls `POST /v1/compare`.

Each candidate remains independently represented.

The CLI must not:

- rank candidates
- score candidates
- declare a winner
- label a candidate best/worst
- recommend a model
- reorder candidates

It simply renders the API's measurements.

### 39.10 Benchmarks command

`aifootprint benchmarks` consumes the existing benchmark endpoints.

Initial capabilities should include:

~~~text
aifootprint benchmarks list
aifootprint benchmarks get <benchmark_id>
aifootprint benchmarks run <benchmark_id>
~~~

Benchmark output must preserve version, workload definition, ranges, status, confidence and methodology information returned by the API.

### 39.11 Authentication and configuration

The CLI must support API authentication through the existing Python SDK.

Required configuration precedence:

1. explicit command-line option, where provided;
2. environment variable;
3. local CLI configuration;
4. SDK/default behavior where applicable.

At minimum support:

~~~text
AIFOOTPRINT_API_KEY
AIFOOTPRINT_BASE_URL
~~~

Raw API keys must never be:

- printed
- included in normal command output
- written to logs
- embedded in URLs
- included in exception messages
- committed to source control

The local configuration mechanism must use restrictive permissions where the operating system supports them.

### 39.12 Output and automation

Human-readable output is the default.

A machine-readable JSON mode must be available consistently across commands, using a stable flag such as:

~~~text
--output table
--output json
~~~

JSON output must represent the API response semantics without adding ranking, scoring or transformed point estimates.

The CLI must support non-interactive execution suitable for CI/CD.

No command should require a TTY for normal operation.

### 39.13 Exit codes and errors

The CLI must expose deterministic process exit codes.

Initial categories:

| Category | Exit code |
|---|---:|
| Success | 0 |
| Invalid CLI input / API validation | 2 |
| Authentication failure | 3 |
| Authorization failure | 4 |
| Not found | 5 |
| Conflict / idempotency conflict | 6 |
| Rate limited | 7 |
| Server/API failure | 8 |
| Network/transport failure | 9 |
| Configuration error | 10 |

The exact implementation may use a compact stable mapping, but the mapping must be documented and tested.

Human-readable errors must include the API error message and request ID where available, but must never expose credentials.

### 39.14 SDK architecture

The CLI must call the existing `aifootprint` Python SDK.

The CLI must not:

- create a second HTTP client;
- implement bearer authentication independently;
- duplicate API error mapping;
- calculate estimates;
- contain environmental coefficients;
- resolve methodology factors;
- persist its own workload database;
- invent a second idempotency mechanism.

The Python SDK remains the REST boundary.

### 39.15 Client context

Every CLI-submitted event should identify the client surface using Sprint 6:

~~~text
client_type = cli
client_name = aifootprint-cli
client_version = installed CLI version
runtime = non-sensitive runtime identifier
~~~

Client context is observational and must never affect authorization or estimation.

### 39.16 Privacy

The CLI must operate without collecting AI content.

It must not automatically capture:

- prompts
- responses
- source code
- private files
- private images
- private audio/video
- provider credentials

Explicit user-supplied metadata remains subject to the existing workload metadata contract.

### 39.17 CI/CD and scripting

The CLI must be suitable for:

- shell scripts
- CI pipelines
- GitHub Actions or equivalent automation
- developer pre-commit/workflow integrations
- scheduled measurement jobs

Commands must return deterministic exit codes.

JSON output must be parseable without terminal formatting or ANSI escape sequences.

The CLI must not depend on interactive login for API-key based automation.

### 39.18 Packaging and compatibility

The CLI must be installable as a normal Python package.

Target Python compatibility should remain aligned with the existing SDK:

~~~text
Python >= 3.10
~~~

The CLI version must be independently versioned from the AI Footprint API version.

The CLI may depend on the existing SDK and a focused CLI argument/parsing library if justified. It must not introduce unnecessary runtime infrastructure.

### 39.19 Documentation

Documentation must include:

- installation
- configuration
- first event submission
- stateless estimation
- usage inspection
- comparison
- benchmarks
- JSON output
- CI/CD usage
- exit codes
- privacy behavior
- API-key security
- client metadata behavior

A new developer should be able to install the CLI and submit a first workload without reading backend source code.

### 39.20 Testing requirements

#### CLI unit tests

- command discovery/help
- argument validation
- configuration precedence
- missing configuration
- output formatting
- JSON output
- exit-code mapping
- credential redaction
- client metadata generation
- version reporting

#### SDK integration/contract tests

- CLI invokes SDK resources rather than raw HTTP
- event payload includes `client_type=cli`
- omitted optional values are not invented
- request IDs propagate
- API errors propagate correctly
- idempotency key reaches the existing event API
- no CLI-specific estimation path exists

#### End-to-end

At minimum validate:

1. CLI → SDK → `/v1/events`
2. CLI → SDK → `/v1/estimate`
3. CLI → SDK → usage endpoint
4. CLI → SDK → compare
5. CLI → SDK → benchmarks
6. authentication failure
7. authorization failure
8. invalid request
9. rate-limit response
10. server/transport failure
11. JSON output
12. non-interactive execution

#### Regression

- full backend suite
- full SDK suite
- frontend suite
- Ruff
- mypy
- TypeScript/lint/build
- Alembic validation
- CLI package build/install validation

### 39.21 Security requirements

The implementation must demonstrate:

1. no raw API-key persistence outside the explicitly documented local configuration mechanism;
2. restrictive local configuration permissions where supported;
3. no API key in process output;
4. no API key in error messages;
5. no API key in URLs;
6. no credential logging;
7. no prompt/response capture;
8. client metadata cannot alter project or application authorization;
9. CLI uses existing backend authorization;
10. dependencies are kept minimal and security-scanned.

### 39.22 Explicit non-goals

Sprint 7 does not include:

- Browser Extension
- Chrome/Firefox extension distribution
- iOS application
- Android application
- automatic provider traffic interception
- provider credential capture
- prompt/response storage
- source-code indexing
- new provider integrations
- new environmental coefficients
- new estimation algorithms
- local footprint calculation
- model ranking
- scoring
- recommendation engine
- optimization
- routing
- billing
- RBAC
- SSO
- enterprise gateway
- Redis
- Kafka
- data warehouse
- Kubernetes
- new backend instrumentation endpoint
- a second HTTP/authentication stack

### 39.23 Definition of Done

Sprint 7 is complete when:

1. `aifootprint` installs successfully.
2. Help and version commands work.
3. Event submission works through the existing API.
4. Stateless estimation works through the existing API.
5. Usage inspection works.
6. Compare works.
7. Benchmarks work.
8. CLI events carry `client_type=cli`.
9. Configuration and authentication are documented and tested.
10. JSON and human-readable output work.
11. Exit codes are deterministic and documented.
12. Request IDs are visible where available.
13. API keys are not leaked.
14. CLI is non-interactive and CI/CD friendly.
15. CLI uses the Python SDK rather than a second HTTP client.
16. No estimation logic or environmental factors are introduced.
17. Existing backend, SDK and frontend behavior remains backward compatible.
18. Full automated regression and CLI validation pass.
19. CLI documentation enables a new developer to complete a first measurement without repository knowledge.

### 39.24 Deliverables

~~~text
cli/
  aifootprint CLI package
  commands
  configuration
  output formatting
  tests

sdk/
  only additive changes required for CLI integration

docs/
  Sprint 7 PRD/FRD updates
  CLI Quick Start
  CLI reference
  CI/CD examples
  security/privacy guidance
~~~

No Browser Extension or Mobile source tree is required in Sprint 7.
