import pytest

from app.methodology.dto import MetricEstimate
from app.methodology.uncertainty import UncertaintyEngine
from app.models.enums import MetricStatus


def test_aggregate_sums_min_and_max_independently():
    estimates = [
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.01, max=0.02),
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.03, max=0.10),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    assert aggregated.status == MetricStatus.OK
    assert aggregated.min == pytest.approx(0.04)
    assert aggregated.max == pytest.approx(0.12)


def test_aggregate_ignores_insufficient_data_entries():
    estimates = [
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.01, max=0.02),
        MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit="Wh"),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    assert aggregated.status == MetricStatus.OK
    assert aggregated.min == 0.01
    assert aggregated.max == 0.02


def test_aggregate_returns_insufficient_data_when_nothing_available():
    aggregated = UncertaintyEngine.aggregate([], unit="Wh")

    assert aggregated.status == MetricStatus.INSUFFICIENT_DATA
    assert aggregated.min is None
    assert aggregated.max is None


def test_aggregate_never_averages():
    estimates = [
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.0, max=10.0),
        MetricEstimate(status=MetricStatus.OK, unit="Wh", min=0.0, max=10.0),
    ]

    aggregated = UncertaintyEngine.aggregate(estimates, unit="Wh")

    # A naive average would (incorrectly) report max=10.0 again; additive
    # aggregation must report max=20.0.
    assert aggregated.max == 20.0
