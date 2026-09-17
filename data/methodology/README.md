# Methodology Factor Data Contract v0.1

This directory contains versioned methodology factors used by the Footprint Engine.

## Rules

- Factors are data, not application code.
- Every factor requires provenance.
- Every factor has an evidence level and confidence.
- Factors are time-versioned.
- Do not add a factor solely from an unsourced web claim.
- Do not use a generic factor when a more specific approved factor exists.
- Do not overwrite historical factors; add a new effective version.

## Canonical fields

```yaml
factor_id: string
methodology_version: string
metric: energy|water|carbon
provider: string|null
model: string|null
modality: text|image|video|audio|coding|agent|other
activity_type: string
region: string|null
hardware: string|null
value_min: number
value_max: number
unit: Wh|mL|gCO2e
evidence_level: 1|2|3|4|5|6
confidence: high|medium|low
source: string
source_date: YYYY-MM-DD
accounting_boundary: A|B|C
effective_from: YYYY-MM-DD
effective_to: YYYY-MM-DD|null
assumptions:
  - string
limitations:
  - string
```

## Factor resolution precedence

1. Provider + model + activity + region + hardware
2. Provider + model + activity
3. Provider + modality + activity
4. Model/hardware research factor
5. Approved generic workload factor
6. No factor → `insufficient_data`

The engine must record which factor was selected in the estimate provenance.

## Example provider-reported record

This is a schema example only; it is not a universal coefficient:

```yaml
factor_id: google-gemini-apps-median-text-may-2025-energy
methodology_version: "0.1"
metric: energy
provider: google
model: gemini-apps
modality: text
activity_type: text_generation
region: global-provider-fleet
hardware: null
value_min: 0.24
value_max: 0.24
unit: Wh
evidence_level: 1
confidence: high
source: https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference
source_date: 2025-08-21
accounting_boundary: B
effective_from: 2025-05-01
effective_to: null
assumptions:
  - Point-in-time median Gemini Apps text-generation prompt.
limitations:
  - Not representative of every Gemini request.
  - Not a universal LLM coefficient.
```

The same evidence may have separate records for water and carbon because each metric has its own unit and calculation provenance.

## Do not add production coefficients yet

Before adding broad model coefficients, the team must review and approve the evidence and define the workload scope. The first implementation should prove the data contract and calculation engine using fixtures/tests rather than invented constants.
