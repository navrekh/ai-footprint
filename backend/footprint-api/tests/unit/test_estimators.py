from datetime import date

from app.methodology.estimators import CarbonEstimator, EnergyEstimator, WaterEstimator
from app.models.enums import Confidence, MetricStatus
from app.models.methodology_factor import MethodologyFactor


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
        source="TEST_ONLY",
        source_date=date(2020, 1, 1),
        accounting_boundary="A",
        effective_from=date(2020, 1, 1),
        methodology_version="TEST_ONLY-0.1",
        assumptions=["TEST_ONLY"],
        limitations=[],
    )
    defaults.update(overrides)
    return MethodologyFactor(**defaults)


def test_energy_estimator_uses_factor_values_directly():
    estimate = EnergyEstimator().estimate(_factor())

    assert estimate.status == MetricStatus.OK
    assert estimate.min == 0.01
    assert estimate.max == 0.02
    assert estimate.unit == "Wh"
    assert estimate.confidence == Confidence.LOW


def test_water_estimator_insufficient_data_without_factor():
    estimate = WaterEstimator().estimate(None)

    assert estimate.status == MetricStatus.INSUFFICIENT_DATA
    assert estimate.min is None
    assert estimate.max is None
    assert estimate.unit == "mL"


def test_carbon_estimator_insufficient_data_without_factor():
    estimate = CarbonEstimator().estimate(None)

    assert estimate.status == MetricStatus.INSUFFICIENT_DATA
    assert estimate.unit == "gCO2e"
