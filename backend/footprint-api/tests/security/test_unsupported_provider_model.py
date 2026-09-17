import pytest

from tests import factories


@pytest.mark.asyncio
async def test_unsupported_provider_returns_provider_not_found(client, auth_headers):
    payload = {
        "provider": "totally-unsupported-provider",
        "model": "some-model",
        "modality": "text",
        "activity_type": "text_generation",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROVIDER_NOT_FOUND"


@pytest.mark.asyncio
async def test_unsupported_model_returns_model_not_found(client, auth_headers, db_session):
    await factories.create_provider(db_session, "openai", modalities=["text"])
    await db_session.commit()

    payload = {
        "provider": "openai",
        "model": "totally-unsupported-model",
        "modality": "text",
        "activity_type": "text_generation",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"


@pytest.mark.asyncio
async def test_deprecated_model_returns_model_not_supported(client, auth_headers, db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, status="deprecated")
    await db_session.commit()

    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MODEL_NOT_SUPPORTED"


@pytest.mark.asyncio
async def test_model_not_supporting_requested_modality_returns_model_not_supported(
    client, auth_headers, db_session
):
    provider = await factories.create_provider(db_session, "openai", modalities=["text", "image"])
    await factories.create_model(db_session, provider_id=provider.id, modalities=["text"])
    await db_session.commit()

    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "image",
        "activity_type": "image_generation",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MODEL_NOT_SUPPORTED"
