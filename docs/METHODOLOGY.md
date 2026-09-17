# AI Footprint — Resource Impact Methodology v0.1

**Status:** Proposed MVP methodology

## 1. Purpose

AI Footprint estimates the resource impact of AI workloads. It reports **ranges**, **confidence**, **evidence level**, **methodology version**, and **assumptions** rather than presenting modeled values as exact measurements.

The core chain is:

`AIWorkload → Energy → Water → CO₂e → uncertainty/confidence`

## 2. Core principles

1. Never claim an exact physical measurement when only an estimate is available.
2. Never use a universal "water per prompt" coefficient.
3. Prefer provider-reported production measurements when their scope matches the workload.
4. Otherwise use documented empirical research or an explicit engineering model.
5. Preserve provenance for every factor.
6. Version all factors and methodologies; never silently overwrite historical assumptions.
7. Return `insufficient_data` when evidence is inadequate rather than inventing a number.
8. Minimize user-content collection; measurement should primarily use workload metadata.

## 3. Accounting boundaries

v0.1 distinguishes:

### Boundary A — AI inference operations

Energy directly associated with serving the workload.

### Boundary B — data-center operational footprint

Adds relevant host/system energy and facility overhead such as cooling and power distribution.

### Boundary C — lifecycle footprint

May include embodied hardware and infrastructure impacts. **Not part of the MVP unless adequate evidence exists.**

The API must identify the accounting boundary used by each estimate.

## 4. Evidence hierarchy

Each methodology factor has an evidence level:

| Level | Evidence |
|---|---|
| 1 | Direct measured production data |
| 2 | Provider technical disclosure/methodology |
| 3 | Peer-reviewed empirical measurement |
| 4 | Independent technical benchmark/study |
| 5 | Engineering model based on documented assumptions |
| 6 | Proxy assumption |

A higher-quality source should supersede a weaker source only when workload scope, accounting boundary and time period are comparable.

## 5. Energy

Energy is the primary physical metric and is stored in Wh.

Energy must not be modeled as a universal `tokens × constant` formula. Relevant variables can include:

- provider
- model
- modality
- input/output tokens
- image count and resolution
- video duration/resolution
- audio duration
- tool calls
- reasoning/agent behavior
- hardware
- utilization
- data-center overhead

The engine should resolve the most specific applicable factor and produce a minimum/maximum estimate.

## 6. Text and reasoning

Text workloads use token counts when available, but token count alone does not determine energy.

The taxonomy distinguishes:

- `text_generation`
- `text_reasoning`
- `agent_workflow`
- `coding_agent`

Reasoning and agentic workloads must not automatically inherit standard text coefficients because their computation may be substantially different.

## 7. Image

Image workloads are modeled separately. Relevant parameters include:

- model
- operation
- image count
- width
- height
- inference steps, when available

Supported activity types include:

- `image_generation`
- `image_editing`
- `image_enhancement`

## 8. Video

Video is modeled separately because resource use varies substantially with duration, resolution, frame rate, model and generation mode.

Where empirical evidence is weak, uncertainty should widen and confidence should decrease.

## 9. Audio

Audio workloads include speech-to-text, text-to-speech and generative audio. Duration and model are preferred workload parameters.

## 10. Coding and agents

Coding is a first-class workload category:

- code generation
- code review
- debugging
- test generation
- refactoring
- repository analysis
- coding agents

Agent sessions should aggregate child inference events. A single user request may result in many model calls and tool calls; the initial prompt must not be treated as the complete workload.

## 11. Water

The primary consumer-facing water metric is **estimated water consumption**, not withdrawal.

Water may include:

1. data-center operational/cooling water consumption; and
2. water associated with electricity generation where the accounting boundary includes it.

Water is stored in mL.

Water intensity is location-, cooling- and infrastructure-dependent. If serving location or provider-specific water data is unknown, the methodology must explicitly identify the generalized assumption used.

Water scarcity/stress weighting is a separate future metric and must not be silently mixed into physical water consumption in v0.1.

## 12. Carbon

Carbon is stored as gCO₂e.

For workloads where direct provider emissions are unavailable, operational electricity emissions may be estimated from:

`energy × applicable electricity emissions factor`

The default consumer calculation should use a clearly labeled location-based/regional factor when geography is available. Enterprise reporting may support both location-based and market-based approaches when sufficient data exists.

## 13. Uncertainty

Every environmental metric should support:

- `min`
- `max`
- unit

For additive composite workloads, minimums and maximums are aggregated consistently rather than collapsing uncertainty into a falsely precise mean.

## 14. Confidence

Confidence values:

- `high` — direct/provider production measurement with closely matching scope and workload
- `medium` — strong empirical evidence or validated model with limited unknowns
- `low` — proxy or engineering estimate with material uncertainty

Confidence is not a statistical probability.

## 15. Provider-specific data

Provider-reported measurements may override generic estimates when their methodology is sufficiently documented and applicable.

For example, Google's 2025 production methodology reported a median Gemini Apps text prompt at 0.24 Wh, 0.26 mL water and 0.03 gCO₂e for a May 2025 point-in-time analysis. Those values are **not universal coefficients** for all Gemini requests, all Google workloads, or other providers. They are stored as provider-specific evidence with a defined workload, time period and accounting methodology.

## 16. Methodology record

Every factor should contain:

```text
factor_id
metric
provider
model
modality
activity_type
region
hardware
value_min
value_max
unit
evidence_level
confidence
source
source_date
effective_from
effective_to
methodology_version
assumptions
limitations
```

## 17. Source requirements

Every non-trivial factor must have a source. Preferred sources include:

- peer-reviewed research
- technical papers
- provider engineering/sustainability publications
- IEA or other recognized energy datasets
- GHG Protocol standards/guidance
- government datasets
- recognized environmental datasets

## 18. Unknown data

If a workload cannot be supported responsibly, return a structured `insufficient_data` result. Never fabricate a coefficient merely to complete a response.

## 19. Versioning

Methodology versions are immutable. A changed coefficient, accounting boundary or substantive assumption creates a new methodology version.

Historical estimates retain the methodology version used when calculated.

## 20. Data freshness

Factors should contain `effective_from`, `effective_to`, `last_reviewed` and `next_review` where applicable. AI efficiency, infrastructure and electricity data can change materially over time.

## 21. Consumer communication

Preferred wording:

- "Estimated resource impact"
- "Estimated water consumption"
- "Based on methodology v0.x"
- "Confidence: Medium"

Avoid:

- "This prompt used exactly X mL of water"
- guilt-based language such as "you wasted X litres"

## 22. Methodology references

Initial evidence base includes Google's production AI-serving methodology, which explicitly accounts for accelerator power, host energy, idle capacity and data-center overhead and reports a May 2025 median Gemini Apps text prompt of 0.24 Wh and 0.26 mL water. citeturn0search0turn0academia25

For corporate electricity emissions accounting, AI Footprint should align terminology with the GHG Protocol distinction between location-based and market-based Scope 2 methods. The GHG Protocol is currently revising its Scope 2 guidance, so methodology versions must record the applicable standard/guidance version and date. citeturn0search24turn0search7turn0search2

## 23. MVP calculation rule

The MVP engine must calculate only where an approved factor exists for the workload. It should resolve:

`provider/model/activity/region → factor → energy → water/carbon → range/confidence`

No hard-coded environmental constants belong in controllers, API routes or UI code.
