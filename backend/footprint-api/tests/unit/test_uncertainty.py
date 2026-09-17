import pytest

from app.methodology.dto import MetricEstimate
from app.methodology.uncertainty import UncertaintyEngine
from app.models.enums import Confidence, MetricStatus


def test_aggregate_sums_min_and_max_independently():
    estimates = [
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.01, max=0.02),
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.03, max=0.10),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    assert aggregated.status == MetricStatus.OK
    assert aggregated.min == pytest.approx(0.04)
    assert aggregated.max == pytest.approx(0.12)
    assert aggregated.total_workloads == 2
    assert aggregated.measured_workloads == 2


def test_aggregate_of_mixed_availability_is_partial_not_ok():
    """Sprint review item 3: a partial aggregate must never look complete."""
    estimates = [
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.01, max=0.02),
        MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit="Wh"),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    assert aggregated.status == MetricStatus.PARTIAL
    assert aggregated.min == 0.01
    assert aggregated.max == 0.02
    assert aggregated.total_workloads == 2
    assert aggregated.measured_workloads == 1


def test_aggregate_returns_insufficient_data_when_nothing_available():
    aggregated = UncertaintyEngine.aggregate([], unit="Wh")

    assert aggregated.status == MetricStatus.INSUFFICIENT_DATA
    assert aggregated.min is None
    assert aggregated.max is None
    assert aggregated.total_workloads == 0
    assert aggregated.measured_workloads == 0


def test_aggregate_all_insufficient_is_insufficient_data_not_partial():
    estimates = [
        MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit="Wh"),
        MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit="Wh"),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    assert aggregated.status == MetricStatus.INSUFFICIENT_DATA
    assert aggregated.min is None
    assert aggregated.max is None
    assert aggregated.total_workloads == 2
    assert aggregated.measured_workloads == 0


def test_aggregate_never_averages():
    estimates = [
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.0, max=10.0),
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.0, max=10.0),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    # A naive average would (incorrectly) report max=10.0 again; additive
    # aggregation must report max=20.0.
    assert aggregated.max == 20.0


def test_aggregate_preserves_confidence_and_evidence_metadata():
    """Sprint review item 4: aggregation must not drop confidence/evidence."""
    estimates = [
        MetricEstimate(
            status=MetricStatus.OK,
            unit="Wh",
            min=0.01,
            max=0.02,
            confidence=Confidence.LOW,
            evidence_level=6,
            accounting_boundary="A",
            assumptions=["TEST_ONLY fixture - not a real measurement."],
        )
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    assert aggregated.confidence == Confidence.LOW
    assert aggregated.evidence_level == 6
    assert aggregated.accounting_boundary == "A"
    assert aggregated.assumptions == ["TEST_ONLY fixture - not a real measurement."]


def test_aggregate_combines_confidence_across_multiple_estimates():
    estimates = [
        MetricEstimate(
            status=MetricStatus.OK, unit="Wh", min=0.01, max=0.02, confidence=Confidence.HIGH
        ),
        MetricEstimate(
            status=MetricStatus.OK, unit="Wh", min=0.01, max=0.02, confidence=Confidence.LOW
        ),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    # Combined confidence is never stronger than its weakest contributor.
    assert aggregated.confidence == Confidence.LOW
