import pytest


@pytest.mark.asyncio
async def test_missing_required_field_returns_missing_parameter(client, auth_headers):
    payload = {
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MISSING_PARAMETER"
    assert "request_id" in response.json()["error"]


@pytest.mark.asyncio
async def test_invalid_enum_value_returns_invalid_request(client, auth_headers):
    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "not-a-real-modality",
        "activity_type": "text_generation",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_negative_quantity_is_rejected(client, auth_headers):
    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": -5,
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_non_json_body_returns_error_without_stack_trace(client, auth_headers):
    response = await client.post(
        "/v1/estimate",
        content=b"not-json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert "Traceback" not in body["error"]["message"]
