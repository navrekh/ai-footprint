"""SDK-contract tests for `aifootprint estimate`."""

from __future__ import annotations

import json

from aifootprint_cli.cli import main

BASE = [
    "estimate",
    "--provider",
    "openai",
    "--model",
    "model-id",
    "--modality",
    "text",
    "--activity-type",
    "text_generation",
]

RESPONSE = {
    "estimate_id": "est_1",
    "energy": {"status": "ok", "min": 10.0, "max": 20.0, "unit": "Wh"},
    "water": {"status": "ok", "min": 30.0, "max": 50.0, "unit": "mL"},
    "carbon": {"status": "ok", "min": 5.0, "max": 8.0, "unit": "gCO2e"},
    "confidence": "medium",
    "evidence_level": 3,
    "accounting_boundary": "B",
    "methodology_version": "0.1",
    "assumptions": ["assumption A"],
    "created_at": "2026-01-01T00:00:00Z",
}


def test_estimate_hits_the_stateless_endpoint(httpx_mock, api_env):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/estimate", json=RESPONSE)

    exit_code = main(BASE)

    assert exit_code == 0
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/v1/estimate"


def test_estimate_never_calls_events_endpoint(httpx_mock, api_env):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/estimate", json=RESPONSE)

    main(BASE)

    assert all(r.url.path != "/v1/events" for r in httpx_mock.get_requests())


def test_range_output_shows_min_and_max_not_an_average(httpx_mock, api_env, capsys):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/estimate", json=RESPONSE)

    main(BASE)
    captured = capsys.readouterr()

    assert "10–20 Wh" in captured.out
    assert "15 Wh" not in captured.out  # the average must never appear


def test_insufficient_data_is_rendered_explicitly_not_as_zero(httpx_mock, api_env, capsys):
    response = {
        **RESPONSE,
        "energy": {"status": "insufficient_data", "min": None, "max": None, "unit": "Wh"},
    }
    httpx_mock.add_response(method="POST", url="http://testserver/v1/estimate", json=response)

    main(BASE)
    captured = capsys.readouterr()

    assert "Insufficient data" in captured.out
    assert "Energy: 0" not in captured.out


def test_json_output_preserves_all_provenance_fields(httpx_mock, api_env, capsys):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/estimate", json=RESPONSE)

    main([*BASE, "--output", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["confidence"] == "medium"
    assert data["evidence_level"] == 3
    assert data["accounting_boundary"] == "B"
    assert data["methodology_version"] == "0.1"
    assert data["assumptions"] == ["assumption A"]


def test_validation_error_maps_to_exit_code_2(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/estimate",
        status_code=422,
        json={
            "error": {"code": "INVALID_WORKLOAD", "message": "Bad workload.", "request_id": "req_y"}
        },
    )

    exit_code = main(BASE)
    assert exit_code == 2
