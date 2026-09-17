from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import InvalidDateRangeError
from app.methodology.uncertainty import determine_metric_status
from app.models.enums import MetricStatus
from app.services.usage_service import DEFAULT_LOOKBACK_DAYS, resolve_period


def test_determine_metric_status_none_measured_is_insufficient_data():
    assert determine_metric_status(total=5, measured=0) == MetricStatus.INSUFFICIENT_DATA


def test_determine_metric_status_all_measured_is_ok():
    assert determine_metric_status(total=5, measured=5) == MetricStatus.OK


def test_determine_metric_status_some_measured_is_partial():
    assert determine_metric_status(total=5, measured=2) == MetricStatus.PARTIAL


def test_determine_metric_status_zero_total_is_insufficient_data():
    assert determine_metric_status(total=0, measured=0) == MetricStatus.INSUFFICIENT_DATA


def test_resolve_period_defaults_to_lookback_window():
    resolved_from, resolved_to = resolve_period(None, None)

    assert (resolved_to - resolved_from) == timedelta(days=DEFAULT_LOOKBACK_DAYS)


def test_resolve_period_uses_supplied_bounds():
    from_ts = datetime(2026, 1, 1, tzinfo=UTC)
    to_ts = datetime(2026, 1, 31, tzinfo=UTC)

    resolved_from, resolved_to = resolve_period(from_ts, to_ts)

    assert resolved_from == from_ts
    assert resolved_to == to_ts


def test_resolve_period_rejects_from_after_to():
    from_ts = datetime(2026, 6, 1, tzinfo=UTC)
    to_ts = datetime(2026, 1, 1, tzinfo=UTC)

    with pytest.raises(InvalidDateRangeError):
        resolve_period(from_ts, to_ts)


def test_resolve_period_defaults_to_only_when_from_given():
    from_ts = datetime(2026, 1, 1, tzinfo=UTC)

    resolved_from, resolved_to = resolve_period(from_ts, None)

    assert resolved_from == from_ts
    assert resolved_to > resolved_from
