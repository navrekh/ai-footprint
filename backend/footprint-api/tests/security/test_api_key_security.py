import pytest

from app.core.security import hash_api_key
from app.models.api_key import ApiKey
from app.models.enums import ApiKeyStatus

VALID_PAYLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 10,
    "output_tokens": 10,
}


@pytest.mark.asyncio
async def test_missing_api_key_rejected_on_every_protected_endpoint(client):
    for method, path, body in [
        ("post", "/v1/estimate", VALID_PAYLOAD),
        ("post", "/v1/events", VALID_PAYLOAD),
        ("post", "/v1/batch-estimate", {"workloads": [VALID_PAYLOAD]}),
    ]:
        response = await getattr(client, method)(path, json=body)
        assert response.status_code == 401, path
        assert response.json()["error"]["code"] == "UNAUTHORIZED", path


@pytest.mark.asyncio
async def test_invalid_api_key_rejected(client):
    response = await client.post(
        "/v1/estimate",
        json=VALID_PAYLOAD,
        headers={"Authorization": "Bearer afp_test_totally-invalid-key"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_revoked_api_key_rejected(client, tenant, db_session, wired_model):
    tenant["api_key"].status = ApiKeyStatus.REVOKED.value
    await db_session.commit()

    response = await client.post(
        "/v1/estimate",
        json=VALID_PAYLOAD,
        headers={"Authorization": f"Bearer {tenant['raw_key']}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_raw_api_key_is_never_persisted(db_session, tenant):
    from sqlalchemy import select

    result = await db_session.execute(select(ApiKey).where(ApiKey.id == tenant["api_key"].id))
    stored = result.scalar_one()

    assert stored.key_hash == hash_api_key(tenant["raw_key"])
    assert tenant["raw_key"] not in stored.key_hash
    assert not hasattr(stored, "raw_key")
