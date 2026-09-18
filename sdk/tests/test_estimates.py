import json

from aifootprint.models import Confidence, Estimate, MetricStatus, PersistedEstimate


def _estimate_body(**overrides) -> dict:
    body = {
        "estimate_id": "est_1",
        "energy": {"status": "ok", "min": 0.31, "max": 0.42, "unit": "Wh"},
        "water": {"status": "ok", "min": 0.28, "max": 0.35, "unit": "mL"},
        "carbon": {"status": "ok", "min": 0.04, "max": 0.06, "unit": "gCO2e"},
        "confidence": "medium",
        "evidence_level": 3,
        "accounting_boundary": "B",
        "methodology_version": "0.1",
        "assumptions": ["Location-based grid emissions factor."],
        "created_at": "2026-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def test_create_sends_correct_path_and_body(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/estimate", json=_estimate_body()
    )
    result = client.estimates.create(
        provider="openai",
        model="model-id",
        modality="text",
        activity_type="text_generation",
        input_tokens=2000,
        output_tokens=1000,
    )

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["provider"] == "openai"
    assert body["model"] == "model-id"
    assert body["modality"] == "text"
    assert body["activity_type"] == "text_generation"
    assert body["input_tokens"] == 2000
    assert body["output_tokens"] == 1000
    # Fields the caller never set are omitted entirely, not sent as null.
    assert "model_version" not in body
    assert "image_count" not in body

    assert isinstance(result, Estimate)
    assert result.estimate_id == "est_1"


def test_range_is_preserved_not_averaged(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/estimate", json=_estimate_body()
    )
    result = client.estimates.create(
        provider="openai", model="m", modality="text", activity_type="text_generation"
    )
    assert result.energy.min == 0.31
    assert result.energy.max == 0.42
    # The SDK never computes or exposes a midpoint - only min/max exist.
    assert not hasattr(result.energy, "value")
    assert not hasattr(result.energy, "average")


def test_confidence_and_methodology_are_preserved(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/estimate", json=_estimate_body()
    )
    result = client.estimates.create(
        provider="openai", model="m", modality="text", activity_type="text_generation"
    )
    assert result.confidence == Confidence.MEDIUM
    assert result.evidence_level == 3
    assert result.methodology_version == "0.1"
    assert result.assumptions == ["Location-based grid emissions factor."]
    assert result.accounting_boundary == "B"


def test_insufficient_data_status_is_preserved_not_converted_to_zero(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/estimate",
        json=_estimate_body(
            energy={"status": "insufficient_data", "min": None, "max": None, "unit": "Wh"},
            confidence=None,
            evidence_level=None,
        ),
    )
    result = client.estimates.create(
        provider="openai", model="m", modality="text", activity_type="text_generation"
    )
    assert result.energy.status == MetricStatus.INSUFFICIENT_DATA
    assert result.energy.min is None
    assert result.energy.max is None
    assert result.confidence is None


def test_get_persisted_estimate(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/estimates/est_1",
        json={
            **_estimate_body(),
            "workload_id": "evt_1",
            "provider": "openai",
            "model": "model-id",
            "model_version": "2026-01-01",
            "status": "measured",
        },
    )
    result = client.estimates.get("est_1")
    assert isinstance(result, PersistedEstimate)
    assert result.workload_id == "evt_1"
    assert result.status == "measured"
