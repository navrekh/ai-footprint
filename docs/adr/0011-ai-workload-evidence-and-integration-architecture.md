# ADR-0011: AI Workload Evidence and Integration Architecture

**Status:** Proposed — owner review required  
**Date:** 2026-09-19  
**Scope:** Cross-cutting architecture for future AI provider, cloud, observability, application, browser and mobile integrations

## Context

AI Footprint is intended to measure the resource footprint of AI workloads across more than developer-authored API calls. AI activity can occur inside AI-native applications, cloud AI services, coding assistants, agentic workflows, image/video generation systems, presentation builders and other products where the final artifact alone does not reveal the underlying AI operations.

The platform must therefore distinguish:

1. **AI activity detection/discovery** — evidence that AI activity occurred.
2. **AI workload measurement** — structured information about the underlying AI operation.
3. **Resource-footprint estimation** — the existing estimation process that converts supported workload measurements into resource-impact ranges.

AI Footprint must not infer exact physical consumption merely from an output artifact such as "one presentation created" or "one application generated." When direct workload evidence is unavailable, the platform must preserve the weaker evidence level and associated uncertainty.

OpenTelemetry is relevant as a provider-neutral interoperability layer. Current OpenTelemetry GenAI semantic conventions expose standardized attributes for provider/model information, operation names, token usage, tool calls and GenAI workflows. Content-bearing attributes are explicitly identified as potentially sensitive, so AI Footprint should prefer metadata-only ingestion by default.

## Decision

### 1. AIWorkload remains the canonical measurement object

All integration paths must normalize into the existing **AIWorkload** abstraction.

Conceptually:

```
Integration / Evidence Source
          ↓
   Normalization Layer
          ↓
       AIWorkload
          ↓
   Existing Estimation Engine
          ↓
 Footprint + uncertainty + provenance
```

No provider, cloud, browser or application integration may create a parallel measurement object that bypasses AIWorkload.

### 2. Evidence provenance becomes a first-class architectural concern

Every externally sourced or inferred workload should be able to carry evidence provenance describing where the workload information came from.

The architecture should support evidence classes such as:

- DIRECT_PROVIDER
- CLOUD_TELEMETRY
- OPENTELEMETRY
- APPLICATION_INTEGRATION
- SDK
- CLI
- BROWSER_OBSERVED
- MOBILE_OBSERVED
- USER_DECLARED
- INFERRED

These are evidence classifications, not quality scores or rankings.

The implementation must not collapse evidence provenance into a single numerical score.

### 3. Direct and inferred evidence must remain distinguishable

Direct/provider/application telemetry may contain model, provider, token, modality, operation or tool information.

Browser/mobile observation may establish that an AI service or activity was observed but generally cannot establish complete server-side model execution details.

Therefore:

- Direct telemetry may support stronger measurement when the required methodology inputs exist.
- Observed/inferred activity must retain its weaker evidence provenance.
- The estimation engine must not silently upgrade inferred activity into direct measurement.
- Artifact-only inference must not be represented as exact physical consumption.

### 4. Integrations are organized into five families

#### A. Model-provider integrations

Examples include OpenAI, Anthropic, Google/Gemini, AWS Bedrock and Azure-hosted AI services.

Primary purpose:
- provider/model identification
- usage metadata
- modality/operation metadata
- provider-specific usage information when available

#### B. Cloud integrations

Examples include AWS, Azure and Google Cloud.

Primary purpose:
- discover AI workloads already running in enterprise cloud environments
- consume authorized telemetry/log/usage data
- attribute workloads to applications, projects or environments where the source provides that information

Cloud integrations must use least-privilege access and must not require prompt/response content for basic measurement.

#### C. Observability integrations

OpenTelemetry is the preferred interoperability concept.

AI Footprint should be able to consume relevant GenAI telemetry where organizations already instrument their applications, rather than requiring duplicate application instrumentation.

The architecture should also allow future adapters for observability platforms such as CloudWatch, Azure Monitor, Google Cloud Observability and other telemetry systems.

#### D. Application integrations

AI-native applications may directly send workload telemetry to AI Footprint.

Examples of future integration categories include:
- AI coding applications
- AI presentation applications
- AI image/video applications
- AI research applications
- AI app builders
- AI agent platforms

The integration contract should allow an application to report multiple underlying AIWorkloads for one user-visible task.

For example, "create a presentation" may produce separate workloads for text generation, image generation, retrieval, layout generation and agent/tool operations when the application can provide that evidence.

#### E. Browser/mobile observation

Browser Extension and mobile integrations are discovery/observation mechanisms, not substitutes for provider telemetry.

They may identify known AI services and observable activity signals while preserving explicit evidence limitations.

They must not claim visibility into server-side model execution that the client cannot actually observe.

### 5. OpenTelemetry is an interoperability layer, not the AI Footprint domain model

AI Footprint should consume relevant OpenTelemetry GenAI attributes where available, but should not make its internal domain model identical to OpenTelemetry.

OpenTelemetry provides telemetry conventions.

AI Footprint provides:
- workload normalization
- methodology
- resource-footprint estimation
- ranges
- confidence/evidence semantics
- provenance
- measurement coverage

This keeps AI Footprint provider-neutral and avoids coupling the product domain to one telemetry standard.

### 6. Privacy-first ingestion is mandatory

Integration paths should prefer:

- provider/model metadata
- token/usage metadata
- operation metadata
- timestamps
- application/environment identifiers
- tool-count/type metadata where sufficient

Prompt, response, source-code, document and tool-argument content must not be required for basic footprint measurement.

If an upstream integration can provide sensitive content, AI Footprint must not assume that content capture is necessary.

### 7. Multiple AIWorkloads may represent one user-visible activity

The platform must not equate a user-visible artifact with a single AIWorkload.

A higher-level task may contain multiple workloads:

```
User Task
  ├── text generation
  ├── retrieval
  ├── image generation
  ├── tool execution
  ├── code generation
  └── finalization
```

Where integration evidence supports this decomposition, AI Footprint should preserve the individual workloads and aggregate their estimates without losing range semantics or provenance.

### 8. Integration adapters must feed the existing estimation engine

Provider/cloud/observability/application adapters must not contain independent footprint-calculation logic.

The boundary is:

```
Source adapter
    ↓
Normalized AIWorkload
    ↓
Existing methodology / estimation engine
    ↓
Estimate
```

This prevents provider-specific calculations from creating inconsistent resource estimates.

## Consequences

### Positive

- One canonical workload model across SDK, CLI, provider integrations, cloud integrations, OpenTelemetry, browser and mobile.
- Enterprise adoption can eventually begin from existing telemetry rather than requiring application rewrites.
- AI-native applications can provide authoritative workload evidence directly.
- Browser/mobile observation can be useful without pretending to provide provider-level visibility.
- Existing privacy and scientific-humility principles remain intact.
- The architecture can expand to new AI applications without creating a new measurement model for every category.

### Trade-offs

- Integration normalization becomes a significant platform capability.
- Evidence provenance and confidence semantics must remain consistent across adapters.
- Provider/cloud APIs and telemetry schemas evolve independently and require versioned adapters.
- Some integrations will only provide partial evidence and therefore cannot support the same methodology coverage as direct telemetry.
- Enterprise integrations introduce authorization, credential management, tenant isolation and data-governance requirements.

## Explicit non-decisions

This ADR does **not**:

- implement any provider integration;
- implement OpenTelemetry ingestion;
- implement AWS/Azure/GCP connectors;
- implement Browser Extension or mobile applications;
- change the existing estimation methodology;
- add numerical evidence scores;
- add provider/model rankings;
- add artifact-to-resource point estimates;
- require prompt or response capture;
- change the approved Sprint 7A implementation scope by itself.

## Relationship to Sprint 7A

Sprint 7A may continue with CLI distribution and the public developer site.

Before implementing integration-heavy work, future sprints should use this architecture as the boundary for provider, cloud, observability, application, browser and mobile integrations.

The public developer site may describe integrations as roadmap/future capabilities until an integration is actually implemented and verified.

## Future implementation sequence

A future integration program should evaluate, in order:

1. OpenTelemetry-compatible ingestion contract.
2. One major provider/cloud integration.
3. Application integration contract.
4. Additional provider/cloud adapters.
5. Browser discovery/observation.
6. Mobile discovery/observation.

Each integration should have explicit evidence coverage, privacy requirements, authorization model, tenant isolation, failure semantics and test fixtures before production adoption.
