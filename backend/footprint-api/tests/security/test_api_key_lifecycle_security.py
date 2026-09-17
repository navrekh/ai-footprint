from datetime import UTC, datetime, timedelta

import pytest

from tests import factories


@pytest.mark.asyncio
async def test_expired_api_key_rejected_at_http_layer(client, db_session, wired_model):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    _, raw_key = await factories.create_api_key(
        db_session, project.id, expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    await db_session.commit()

    response = await client.get(
        f"/v1/organizations/{org.id}", headers={"Authorization": f"Bearer {raw_key}"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "API_KEY_EXPIRED"


@pytest.mark.asyncio
async def test_wrong_key_is_rejected(client, tenant):
    response = await client.get(
        f"/v1/organizations/{tenant['organization'].id}",
        headers={"Authorization": "Bearer afp_test_wrong-key-value"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_raw_api_key_never_appears_in_logs(client, auth_headers, tenant, caplog):
    with caplog.at_level("INFO"):
        response = await client.post(
            "/v1/api-keys", json={"name": "Should Not Be Logged"}, headers=auth_headers
        )
    raw_key = response.json()["key"]

    for record in caplog.records:
        assert raw_key not in record.getMessage()
        for value in vars(record).values():
            assert raw_key != value


@pytest.mark.asyncio
async def test_raw_api_key_never_appears_in_bootstrap_logs(client, caplog):
    with caplog.at_level("INFO"):
        response = await client.post("/v1/organizations", json={"name": "Quiet Org"})
    raw_key = response.json()["api_key"]["key"]

    for record in caplog.records:
        assert raw_key not in record.getMessage()


@pytest.mark.asyncio
async def test_api_key_read_response_never_includes_hash_or_raw_key(
    client, auth_headers, tenant
):
    response = await client.get("/v1/api-keys", headers=auth_headers)

    raw_text = response.text
    assert "key_hash" not in raw_text
    assert tenant["raw_key"] not in raw_text
