"""Read-only methodology data governance validator (docs/METHODOLOGY.md
section 26, docs/ARCHITECTURE.md ADR-011).

This is advisory tooling for data governance, not a runtime gate and not
a second estimation path: it never calls EstimationPipeline/
FactorRepository, never modifies data, and never invents or infers a
missing value - a missing or inconsistent field is always reported as a
finding, never filled in. EstimationPipeline/FactorRepository remain the
sole runtime authority for what an estimate actually resolves to; this
script only checks the structural integrity and TEST_ONLY-vs-production
classification of the data those components will later read.

Usage: python -m scripts.validate_methodology
Exit code is non-zero if any finding is reported.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActivityType, Modality
from app.models.methodology import Methodology
from app.models.methodology_factor import MethodologyFactor
from app.models.model import Model
from app.models.provider import Provider

TEST_ONLY_MARKER = "TEST_ONLY"

# The raw, un-normalized unit every factor must be stored in - normalized
# per-token/per-image/etc units are computed at read time (app/methodology/
# normalization.py) and must never be baked into stored factor data.
ALLOWED_UNITS: dict[str, str] = {"energy": "Wh", "water": "mL", "carbon": "gCO2e"}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_EVIDENCE_LEVELS = set(range(1, 7))
VALID_ACCOUNTING_BOUNDARIES = {"A", "B", "C"}


@dataclass(frozen=True)
class Finding:
    check: str
    entity: str
    message: str


def classify_factor(factor: MethodologyFactor) -> str:
    """Classifies a factor as "production", "test_only" or "inconsistent".

    Uses the naming convention already established by scripts/seed.py
    (the TEST_ONLY substring in methodology_version/source/factor_id)
    rather than a dedicated schema column, avoiding an unnecessary
    migration for the data volume that exists today (docs/METHODOLOGY.md
    section 26). "inconsistent" means the TEST_ONLY marker appears in
    some but not all of these three fields - i.e. the factor cannot be
    unambiguously classified, which is itself a governance defect.
    """
    markers = {
        "methodology_version": TEST_ONLY_MARKER in (factor.methodology_version or ""),
        "source": TEST_ONLY_MARKER in (factor.source or ""),
        "factor_id": TEST_ONLY_MARKER in (factor.factor_id or ""),
    }
    if all(markers.values()):
        return "test_only"
    if not any(markers.values()):
        return "production"
    return "inconsistent"


def validate_factor(
    factor: MethodologyFactor,
    *,
    known_providers: set[str],
    known_models: dict[str, set[str]],
    known_methodology_versions: set[str],
) -> list[Finding]:
    """Structural/referential checks for a single factor. Never invents or
    infers a value - every check either passes or produces a Finding.
    """
    findings: list[Finding] = []
    entity = factor.factor_id

    if factor.provider is not None and factor.provider not in known_providers:
        findings.append(
            Finding("missing_provider_reference", entity, f"Unknown provider '{factor.provider}'.")
        )

    if factor.model is not None and factor.provider is not None:
        models_for_provider = known_models.get(factor.provider, set())
        if factor.model not in models_for_provider:
            findings.append(
                Finding(
                    "missing_model_reference",
                    entity,
                    f"Unknown model '{factor.model}' for provider '{factor.provider}'.",
                )
            )

    if factor.methodology_version not in known_methodology_versions:
        findings.append(
            Finding(
                "missing_methodology_version",
                entity,
                f"Methodology version '{factor.methodology_version}' does not exist.",
            )
        )

    expected_unit = ALLOWED_UNITS.get(factor.metric)
    if expected_unit is None:
        findings.append(Finding("unsupported_metric", entity, f"Unknown metric '{factor.metric}'."))
    elif factor.unit != expected_unit:
        findings.append(
            Finding(
                "invalid_unit",
                entity,
                f"Unit '{factor.unit}' is not the raw unit '{expected_unit}' for metric "
                f"'{factor.metric}'. Normalized units must never be stored on a factor - "
                "normalization is presentation-layer arithmetic (docs/METHODOLOGY.md section 25).",
            )
        )

    if factor.value_min < 0 or factor.value_max < 0:
        findings.append(Finding("invalid_range", entity, "value_min/value_max must be >= 0."))
    if factor.value_min > factor.value_max:
        findings.append(
            Finding("min_greater_than_max", entity, "value_min is greater than value_max.")
        )

    if not factor.source or not factor.source.strip():
        findings.append(Finding("missing_provenance", entity, "source is empty."))

    if factor.evidence_level not in VALID_EVIDENCE_LEVELS:
        findings.append(
            Finding(
                "missing_evidence_information",
                entity,
                f"evidence_level {factor.evidence_level} is not in the documented 1-6 range.",
            )
        )
    if factor.confidence not in VALID_CONFIDENCES:
        findings.append(
            Finding(
                "missing_evidence_information",
                entity,
                f"confidence '{factor.confidence}' is not one of {sorted(VALID_CONFIDENCES)}.",
            )
        )

    if factor.accounting_boundary not in VALID_ACCOUNTING_BOUNDARIES:
        findings.append(
            Finding(
                "invalid_accounting_boundary",
                entity,
                f"accounting_boundary '{factor.accounting_boundary}' is not one of "
                f"{sorted(VALID_ACCOUNTING_BOUNDARIES)}.",
            )
        )

    valid_activity_types = {a.value for a in ActivityType}
    if factor.activity_type not in valid_activity_types:
        findings.append(
            Finding(
                "unsupported_activity_type",
                entity,
                f"activity_type '{factor.activity_type}' is not a recognized ActivityType.",
            )
        )
    valid_modalities = {m.value for m in Modality}
    if factor.modality not in valid_modalities:
        findings.append(
            Finding(
                "unsupported_modality",
                entity,
                f"modality '{factor.modality}' is not a recognized Modality.",
            )
        )

    if classify_factor(factor) == "inconsistent":
        findings.append(
            Finding(
                "test_only_inconsistent",
                entity,
                "TEST_ONLY marker appears in some but not all of "
                "methodology_version/source/factor_id - this factor cannot be unambiguously "
                "classified as production or TEST_ONLY data.",
            )
        )

    return findings


def find_conflicting_factors(factors: list[MethodologyFactor]) -> list[Finding]:
    """Flags factors sharing the same (metric, provider, model, modality,
    activity_type, region, hardware, methodology_version) scope whose
    effective_from/effective_to windows overlap - the resolver in
    app/methodology/factor_repository.py assumes at most one such factor
    is active on any given date, so an overlap is a genuine data
    integrity defect, not a resolvable ambiguity.
    """
    findings: list[Finding] = []
    groups: dict[tuple, list[MethodologyFactor]] = {}
    for factor in factors:
        key = (
            factor.metric,
            factor.provider,
            factor.model,
            factor.modality,
            factor.activity_type,
            factor.region,
            factor.hardware,
            factor.methodology_version,
        )
        groups.setdefault(key, []).append(factor)

    for group in groups.values():
        if len(group) < 2:
            continue
        for i, first in enumerate(group):
            for second in group[i + 1 :]:
                first_end = first.effective_to or date.max
                second_end = second.effective_to or date.max
                if first.effective_from <= second_end and second.effective_from <= first_end:
                    findings.append(
                        Finding(
                            "duplicate_or_conflicting_factor",
                            f"{first.factor_id} / {second.factor_id}",
                            "Overlapping effective_from/effective_to windows for the same "
                            "metric/provider/model/modality/activity_type/region/hardware/"
                            "methodology_version scope.",
                        )
                    )
    return findings


def validate_methodology_record(methodology: Methodology) -> list[Finding]:
    findings: list[Finding] = []
    entity = methodology.version
    if not methodology.sources:
        findings.append(Finding("missing_provenance", entity, "Methodology has no sources listed."))
    if not methodology.assumptions:
        findings.append(
            Finding("missing_provenance", entity, "Methodology has no assumptions listed.")
        )
    return findings


async def run(session: AsyncSession) -> tuple[list[Finding], dict[str, int]]:
    providers = (await session.execute(select(Provider))).scalars().all()
    models = (await session.execute(select(Model))).scalars().all()
    methodologies = (await session.execute(select(Methodology))).scalars().all()
    factors = (await session.execute(select(MethodologyFactor))).scalars().all()

    known_providers = {p.id for p in providers}
    known_models: dict[str, set[str]] = {}
    for m in models:
        known_models.setdefault(m.provider_id, set()).add(m.name)
    known_methodology_versions = {m.version for m in methodologies}

    findings: list[Finding] = []
    classification_counts = {"production": 0, "test_only": 0, "inconsistent": 0}

    for factor in factors:
        classification_counts[classify_factor(factor)] += 1
        findings.extend(
            validate_factor(
                factor,
                known_providers=known_providers,
                known_models=known_models,
                known_methodology_versions=known_methodology_versions,
            )
        )

    findings.extend(find_conflicting_factors(list(factors)))

    for methodology in methodologies:
        findings.extend(validate_methodology_record(methodology))

    return findings, classification_counts


async def main() -> int:
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        findings, classification_counts = await run(session)

    print("Methodology data governance report")
    print("===================================")
    print(
        f"Factors classified: production={classification_counts['production']} "
        f"test_only={classification_counts['test_only']} "
        f"inconsistent={classification_counts['inconsistent']}"
    )
    print()
    if not findings:
        print("No findings. All methodology data passed structural validation.")
        return 0

    print(f"{len(findings)} finding(s):")
    for finding in findings:
        print(f"  [{finding.check}] {finding.entity}: {finding.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
