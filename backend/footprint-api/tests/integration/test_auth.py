import pytest

VALID_PAYLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 100,
    "output_tokens": 50,
}


@pytest.mark.asyncio
async def test_missing_api_key_is_rejected(client):
    response = await client.post("/v1/estimate", json=VALID_PAYLOAD)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in response.json()["error"]


@pytest.mark.asyncio
async def test_malformed_authorization_header_is_rejected(client):
    response = await client.post(
        "/v1/estimate", json=VALID_PAYLOAD, headers={"Authorization": "not-a-bearer-token"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_invalid_api_key_is_rejected(client):
    response = await client.post(
        "/v1/estimate",
        json=VALID_PAYLOAD,
        headers={"Authorization": "Bearer afp_test_does-not-exist"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_valid_api_key_is_accepted(client, auth_headers, wired_model):
    response = await client.post("/v1/estimate", json=VALID_PAYLOAD, headers=auth_headers)

    assert response.status_code == 200
