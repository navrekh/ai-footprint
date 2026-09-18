"""SDK-contract tests for `aifootprint event` (Sprint 7 FRD section
39.18's "SDK/contract" requirements): calls the SDK's events resource,
carries client_type=cli, propagates the request ID, propagates API
errors, and reaches the idempotency key through unchanged.
"""

from __future__ import annotations

import json

from aifootprint_cli import __version__
from aifootprint_cli.cli import main

BASE = [
    "event",
    "--provider",
    "openai",
    "--model",
    "model-id",
    "--modality",
    "text",
    "--activity-type",
    "text_generation",
]


def _event_response(**overrides) -> dict:
    body = {
        "event_id": "evt_1",
        "workload_id": "evt_1",
        "estimate_id": "est_1",
        "status": "measured",
        "idempotent_replay": False,
    }
    body.update(overrides)
    return body


def test_event_reaches_the_sdk_and_hits_the_correct_endpoint(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/events", json=_event_response()
    )

    exit_code = main([*BASE, "--input-tokens", "2000", "--output-tokens", "1000"])

    assert exit_code == 0
    request = httpx_mock.get_requests()[0]
    assert request.method == "POST"
    assert request.url.path == "/v1/events"


def test_event_carries_client_type_cli_and_the_installed_version(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/events", json=_event_response()
    )

    main(BASE)

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["client"]["client_type"] == "cli"
    assert body["client"]["client_name"] == "aifootprint-cli"
    assert body["client"]["client_version"] == __version__


def test_idempotency_key_reaches_the_event_api(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/events", json=_event_response()
    )

    main([*BASE, "--idempotency-key", "checkout-42"])

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["idempotency_key"] == "checkout-42"


def test_omitted_idempotency_key_is_absent_from_the_request(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/events", json=_event_response()
    )

    main(BASE)

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "idempotency_key" not in body


def test_optional_quantity_fields_omitted_when_not_supplied(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/events", json=_event_response()
    )

    main(BASE)

    body = json.loads(httpx_mock.get_requests()[0].content)
    for field in ("input_tokens", "output_tokens", "image_count", "video_seconds"):
        assert field not in body


def test_request_id_is_rendered_from_the_response_header(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/events",
        json=_event_response(),
        headers={"X-Request-ID": "req_from_header"},
    )

    main(BASE)
    captured = capsys.readouterr()
    assert "req_from_header" in captured.out


def test_idempotent_replay_is_rendered(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/events",
        json=_event_response(idempotent_replay=True),
    )

    main(BASE)
    captured = capsys.readouterr()
    assert "Idempotent replay: yes" in captured.out


def test_api_error_propagates_with_the_correct_exit_code(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/events",
        status_code=404,
        json={
            "error": {
                "code": "PROVIDER_NOT_FOUND",
                "message": "Provider not found.",
                "request_id": "req_x",
            }
        },
    )

    exit_code = main(BASE)
    captured = capsys.readouterr()

    assert exit_code == 5
    assert "Provider not found." in captured.err
    assert "req_x" in captured.err


def test_metadata_json_is_sent_as_an_object(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/events", json=_event_response()
    )

    main([*BASE, "--metadata", '{"env": "ci"}'])

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["metadata"] == {"env": "ci"}


def test_json_output_includes_request_id(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/events",
        json=_event_response(),
        headers={"X-Request-ID": "req_json"},
    )

    main([*BASE, "--output", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["request_id"] == "req_json"
    assert data["event_id"] == "evt_1"
