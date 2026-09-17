from datetime import date

from app.models.methodology import Methodology
from app.models.methodology_factor import MethodologyFactor
from scripts.validate_methodology import (
    classify_factor,
    find_conflicting_factors,
    validate_factor,
    validate_methodology_record,
)

_KNOWN_PROVIDERS = {"openai"}
_KNOWN_MODELS = {"openai": {"test-only-model"}}
_KNOWN_METHODOLOGY_VERSIONS = {"TEST_ONLY-0.1", "0.1"}


def _factor(**overrides) -> MethodologyFactor:
    defaults = dict(
        factor_id="TEST_ONLY-factor",
        metric="energy",
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        value_min=0.01,
        value_max=0.02,
        unit="Wh",
        evidence_level=6,
        confidence="low",
        source="TEST_ONLY - synthetic fixture",
        source_date=date(2020, 1, 1),
        accounting_boundary="A",
        effective_from=date(2020, 1, 1),
        methodology_version="TEST_ONLY-0.1",
        assumptions=["TEST_ONLY"],
        limitations=[],
    )
    defaults.update(overrides)
    return MethodologyFactor(**defaults)


def _validate(factor: MethodologyFactor):
    return validate_factor(
        factor,
        known_providers=_KNOWN_PROVIDERS,
        known_models=_KNOWN_MODELS,
        known_methodology_versions=_KNOWN_METHODOLOGY_VERSIONS,
    )


def test_valid_test_only_data_produces_no_findings():
    factor = _factor()

    assert _validate(factor) == []
    assert classify_factor(factor) == "test_only"


def test_valid_production_shaped_data_produces_no_findings():
    factor = _factor(
        factor_id="prod-openai-model-energy",
        source="OpenAI 2026 sustainability disclosure",
        methodology_version="0.1",
    )

    assert _validate(factor) == []
    assert classify_factor(factor) == "production"


def test_missing_provider_reference_is_flagged():
    factor = _factor(provider="unknown-provider")

    findings = _validate(factor)

    assert any(f.check == "missing_provider_reference" for f in findings)


def test_missing_model_reference_is_flagged():
    factor = _factor(model="unknown-model")

    findings = _validate(factor)

    assert any(f.check == "missing_model_reference" for f in findings)


def test_missing_methodology_version_is_flagged():
    factor = _factor(methodology_version="does-not-exist")

    findings = _validate(factor)

    assert any(f.check == "missing_methodology_version" for f in findings)


def test_invalid_range_negative_values_is_flagged():
    factor = _factor(value_min=-1.0, value_max=0.02)

    findings = _validate(factor)

    assert any(f.check == "invalid_range" for f in findings)


def test_min_greater_than_max_is_flagged():
    factor = _factor(value_min=0.5, value_max=0.1)

    findings = _validate(factor)

    assert any(f.check == "min_greater_than_max" for f in findings)


def test_missing_provenance_is_flagged():
    factor = _factor(source="")

    findings = _validate(factor)

    assert any(f.check == "missing_provenance" for f in findings)


def test_missing_evidence_information_is_flagged_for_bad_evidence_level():
    factor = _factor(evidence_level=99)

    findings = _validate(factor)

    assert any(f.check == "missing_evidence_information" for f in findings)


def test_missing_evidence_information_is_flagged_for_bad_confidence():
    factor = _factor(confidence="extremely-sure")

    findings = _validate(factor)

    assert any(f.check == "missing_evidence_information" for f in findings)


def test_unsupported_activity_type_is_flagged():
    factor = _factor(activity_type="not_a_real_activity")

    findings = _validate(factor)

    assert any(f.check == "unsupported_activity_type" for f in findings)


def test_incompatible_activity_type_and_modality_pair_is_flagged():
    # image_generation is only valid under modality "image" - this factor
    # claims modality "text", which is the same class of error CompareRequest
    # now rejects at request time.
    factor = _factor(activity_type="image_generation", modality="text")

    findings = _validate(factor)

    assert any(f.check == "activity_modality_incompatible" for f in findings)


def test_compatible_activity_type_and_modality_pair_is_not_flagged():
    factor = _factor(activity_type="image_generation", modality="image")

    findings = _validate(factor)

    assert not any(f.check == "activity_modality_incompatible" for f in findings)


def test_invalid_normalization_metadata_is_flagged_for_pre_normalized_unit():
    factor = _factor(unit="Wh/token")

    findings = _validate(factor)

    assert any(f.check == "invalid_unit" for f in findings)


def test_test_only_marker_inconsistent_across_fields_is_flagged():
    factor = _factor(methodology_version="0.1", source="TEST_ONLY fixture value")

    assert classify_factor(factor) == "inconsistent"
    findings = _validate(factor)
    assert any(f.check == "test_only_inconsistent" for f in findings)


def test_duplicate_conflicting_factors_with_overlapping_windows_are_flagged():
    first = _factor(factor_id="f1", effective_from=date(2020, 1, 1), effective_to=None)
    second = _factor(factor_id="f2", effective_from=date(2021, 1, 1), effective_to=None)

    findings = find_conflicting_factors([first, second])

    assert any(f.check == "duplicate_or_conflicting_factor" for f in findings)


def test_non_overlapping_factors_are_not_flagged_as_conflicting():
    first = _factor(
        factor_id="f1", effective_from=date(2020, 1, 1), effective_to=date(2020, 12, 31)
    )
    second = _factor(factor_id="f2", effective_from=date(2021, 1, 1), effective_to=None)

    findings = find_conflicting_factors([first, second])

    assert findings == []


def test_methodology_record_missing_sources_is_flagged():
    methodology = Methodology(
        version="0.1",
        description="test",
        effective_date=date(2020, 1, 1),
        sources=[],
        assumptions=["something"],
        limitations=[],
    )

    findings = validate_methodology_record(methodology)

    assert any(f.check == "missing_provenance" for f in findings)
