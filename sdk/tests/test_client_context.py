"""Sprint 6 - client/integration metadata contract (ClientContext,
ClientType) as implemented by the SDK's events/estimates resources and
Workload response model. This SDK does no estimation of its own -
these tests only verify request serialization and response
deserialization, never a calculation.
"""

import json

from aifootprint.models import ClientContext, ClientType, Event, Workload

CLIENT_KWARGS = {
    "provider": "openai",
    "model": "model-id",
    "modality": "text",
    "activity_type": "text_generation",
}


def _event_body(**overrides) -> dict:
    body = {
        "event_id": "evt_1",
        "workload_id": "evt_1",
        "estimate_id": "est_1",
        "status": "measured",
        "idempotent_replay": False,
    }
    body.update(overrides)
    return body


def _workload_body(**overrides) -> dict:
    body = {
        "id": "evt_1",
        "organization_id": "org_1",
        "project_id": "proj_1",
        "application_id": None,
        "provider": "openai",
        "model": "model-id",
        "model_version": None,
        "modality": "text",
        "activity_type": "text_generation",
        "timestamp": "2026-01-01T00:00:00Z",
        "input_tokens": 100,
        "output_tokens": 50,
        "input_characters": None,
        "output_characters": None,
        "image_count": None,
        "image_width": None,
        "image_height": None,
        "video_seconds": None,
        "video_resolution": None,
        "audio_seconds": None,
        "tool_calls": None,
        "duration_seconds": None,
        "duration_ms": None,
        "parent_workload_id": None,
        "metadata": None,
        "client": None,
        "created_at": "2026-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def test_client_context_object_is_serialized_deterministically(httpx_mock, client):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(
        **CLIENT_KWARGS,
        client=ClientContext(
            client_type=ClientType.PYTHON_SDK,
            client_name="aifootprint-python",
            client_version="0.5.0",
            integration_type="backend_middleware",
            integration_version="1.2.0",
            runtime="python/3.13",
        ),
    )

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["client"] == {
        "client_type": "python_sdk",
        "client_name": "aifootprint-python",
        "client_version": "0.5.0",
        "integration_type": "backend_middleware",
        "integration_version": "1.2.0",
        "runtime": "python/3.13",
    }


def test_client_plain_dict_is_also_accepted(httpx_mock, client):
    """Mirrors how `metadata` already accepts a plain dict - callers are
    never forced to import ClientContext for a simple case.
    """
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(**CLIENT_KWARGS, client={"client_type": "web"})

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["client"] == {"client_type": "web"}


def test_client_enum_member_inside_a_plain_dict_serializes_to_its_value(httpx_mock, client):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(**CLIENT_KWARGS, client={"client_type": ClientType.CLI})

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["client"]["client_type"] == "cli"


def test_client_partial_context_omits_unset_fields(httpx_mock, client):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(**CLIENT_KWARGS, client=ClientContext(client_type=ClientType.IOS))

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["client"] == {"client_type": "ios"}


def test_omitted_client_metadata_is_absent_from_the_request_body(httpx_mock, client):
    """Backward compatibility: a caller who never heard of Sprint 6 must
    produce the exact same request shape as before.
    """
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(**CLIENT_KWARGS)

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "client" not in body


def test_estimates_create_also_accepts_client_metadata(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/estimate",
        json={
            "estimate_id": "est_1",
            "energy": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "Wh"},
            "water": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "mL"},
            "carbon": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "gCO2e"},
            "confidence": "medium",
            "evidence_level": 3,
            "accounting_boundary": "B",
            "methodology_version": "0.1",
            "assumptions": [],
            "created_at": "2026-01-01T00:00:00Z",
        },
    )
    client.estimates.create(**CLIENT_KWARGS, client={"client_type": "direct_api"})

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["client"] == {"client_type": "direct_api"}


def test_workload_response_deserializes_client_metadata(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/workloads/evt_1",
        json=_workload_body(
            client={
                "client_type": "browser_extension",
                "client_name": "aifootprint-extension",
                "client_version": "9.9.9",
                "integration_type": None,
                "integration_version": None,
                "runtime": None,
            }
        ),
    )
    result = client.workloads.get("evt_1")

    assert isinstance(result, Workload)
    assert isinstance(result.client, ClientContext)
    assert result.client.client_type == ClientType.BROWSER_EXTENSION
    assert result.client.client_name == "aifootprint-extension"


def test_workload_response_without_client_metadata_deserializes_to_none(httpx_mock, client):
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/workloads/evt_1", json=_workload_body()
    )
    result = client.workloads.get("evt_1")
    assert result.client is None


def test_event_result_ignores_client_metadata_it_was_not_asked_to_return(httpx_mock, client):
    """POST /v1/events returns only ids/status - Event has no `client`
    field, and this must not raise even if extra data were present.
    """
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    result = client.events.create(**CLIENT_KWARGS, client={"client_type": "web"})
    assert isinstance(result, Event)
    assert result.event_id == "evt_1"
