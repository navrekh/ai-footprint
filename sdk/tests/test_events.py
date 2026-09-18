import json

from aifootprint.models import Event


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


def test_create_sends_correct_path_and_body(httpx_mock, client):
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    result = client.events.create(
        provider="openai",
        model="model-id",
        modality="text",
        activity_type="text_generation",
        project_id="proj_1",
        application_id="app_1",
        input_tokens=2000,
        output_tokens=1000,
    )

    request = httpx_mock.get_requests()[0]
    assert request.method == "POST"
    assert request.url.path == "/v1/events"
    body = json.loads(request.content)
    assert body["project_id"] == "proj_1"
    assert body["application_id"] == "app_1"
    assert body["provider"] == "openai"

    assert isinstance(result, Event)
    assert result.event_id == "evt_1"
    assert result.idempotent_replay is False


def test_idempotency_key_is_sent_as_a_body_field_not_a_header(httpx_mock, client):
    """Verified against the actual backend contract
    (app/schemas/workload.py's EventCreateRequest.idempotency_key) - it
    is a JSON body field, not an HTTP header. This test would fail if
    that assumption were ever wrong.
    """
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(
        provider="openai",
        model="model-id",
        modality="text",
        activity_type="text_generation",
        idempotency_key="checkout-session-123",
    )

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["idempotency_key"] == "checkout-session-123"
    # Not sent as a header under any of the conventional idempotency
    # header names - it is exclusively a body field for this API.
    assert "idempotency-key" not in request.headers


def test_idempotent_replay_is_surfaced_on_the_result(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/events",
        json=_event_body(idempotent_replay=True),
    )
    result = client.events.create(
        provider="openai",
        model="m",
        modality="text",
        activity_type="text_generation",
        idempotency_key="same-key-again",
    )
    assert result.idempotent_replay is True
    # Replay returns the *original* ids, unchanged - the SDK does not
    # regenerate or alter them.
    assert result.event_id == "evt_1"
    assert result.estimate_id == "est_1"


def test_sdk_never_generates_an_idempotency_key_on_its_own(httpx_mock, client):
    """When the caller omits idempotency_key entirely, the SDK must not
    invent one - the field must be genuinely absent from the request.
    """
    httpx_mock.add_response(method="POST", url="http://testserver/v1/events", json=_event_body())
    client.events.create(
        provider="openai", model="m", modality="text", activity_type="text_generation"
    )
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "idempotency_key" not in body


def test_status_can_be_partial_or_insufficient_data(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/events",
        json=_event_body(status="insufficient_data"),
    )
    result = client.events.create(
        provider="openai", model="m", modality="text", activity_type="text_generation"
    )
    assert result.status == "insufficient_data"
