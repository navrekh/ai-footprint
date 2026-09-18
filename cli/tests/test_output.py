"""Output-formatting invariants (Sprint 7 FRD section 39.10): ranges are
never averaged, insufficient data is never shown as zero, JSON is
always valid and ANSI-free, and the request ID survives into JSON.
"""

from __future__ import annotations

import json

from aifootprint.models import AggregateMetricRange, Estimate, MetricRange

from aifootprint_cli.output import format_range, format_workload_counts, to_json_dict


def test_ok_range_shows_both_min_and_max():
    range_ = MetricRange(status="ok", min=10.0, max=20.0, unit="Wh")
    assert format_range(range_) == "10–20 Wh"


def test_range_is_never_collapsed_to_a_single_average_value():
    range_ = MetricRange(status="ok", min=10.0, max=20.0, unit="Wh")
    rendered = format_range(range_)
    assert "15" not in rendered  # the average would be 15 - must never appear


def test_insufficient_data_renders_as_explicit_text_never_zero():
    range_ = MetricRange(status="insufficient_data", min=None, max=None, unit="Wh")
    rendered = format_range(range_)
    assert rendered == "Insufficient data"
    assert "0" not in rendered


def test_partial_status_with_a_range_still_shows_the_range():
    range_ = AggregateMetricRange(
        status="partial", min=5.0, max=8.0, unit="mL", total_workloads=10, measured_workloads=4
    )
    assert format_range(range_) == "5–8 mL"


def test_none_range_renders_as_insufficient_data():
    assert format_range(None) == "Insufficient data"


def test_workload_counts_never_hides_coverage():
    counts_text = format_workload_counts(
        _counts(total=100, measured=70, partial=25, insufficient_data=5, coverage_percent=70.0)
    )
    assert "100" in counts_text
    assert "70" in counts_text
    assert "25" in counts_text
    assert "5" in counts_text
    assert "70.0%" in counts_text


def _counts(**kwargs):
    from types import SimpleNamespace

    return SimpleNamespace(**kwargs)


def test_json_output_is_valid_json_with_no_ansi_codes():
    estimate = Estimate(
        estimate_id="est_1",
        energy=MetricRange(status="ok", min=1.0, max=2.0, unit="Wh"),
        water=MetricRange(status="ok", min=1.0, max=2.0, unit="mL"),
        carbon=MetricRange(status="ok", min=0.1, max=0.2, unit="gCO2e"),
        confidence="medium",
        evidence_level=3,
        accounting_boundary="B",
        methodology_version="0.1",
        assumptions=["assumption"],
        created_at="2026-01-01T00:00:00Z",
    )
    estimate.request_id = "req_abc"

    data = to_json_dict(estimate)
    serialized = json.dumps(data)

    json.loads(serialized)  # raises if not valid JSON
    assert "\x1b[" not in serialized  # no ANSI escape codes
    assert data["request_id"] == "req_abc"


def test_json_output_never_introduces_ranking_score_or_recommendation_fields():
    estimate = Estimate(
        estimate_id="est_1",
        energy=MetricRange(status="ok", min=1.0, max=2.0, unit="Wh"),
        water=MetricRange(status="ok", min=1.0, max=2.0, unit="mL"),
        carbon=MetricRange(status="ok", min=0.1, max=0.2, unit="gCO2e"),
        confidence="medium",
        evidence_level=3,
        accounting_boundary="B",
        methodology_version="0.1",
        assumptions=[],
        created_at="2026-01-01T00:00:00Z",
    )
    data = to_json_dict(estimate)
    forbidden = {"rank", "score", "winner", "recommendation", "best"}
    assert forbidden.isdisjoint(data.keys())
