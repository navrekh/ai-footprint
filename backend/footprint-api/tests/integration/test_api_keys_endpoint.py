import pytest


@pytest.mark.asyncio
async def test_create_organization_level_api_key(client, auth_headers, tenant):
    response = await client.post(
        "/v1/api-keys", json={"name": "Org Level Key"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Org Level Key"
    assert body["key"].startswith("afp_test_")
    assert "key_hash" not in body
    assert "raw_key" not in body


@pytest.mark.asyncio
async def test_create_project_scoped_api_key(client, auth_headers, tenant):
    response = await client.post(
        "/v1/api-keys",
        json={"name": "Project Key", "project_id": tenant["project"].id},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["key"].startswith("afp_test_")


@pytest.mark.asyncio
async def test_create_api_key_for_foreign_project_is_not_found(client, auth_headers, db_session):
    from tests import factories

    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    await db_session.commit()

    response = await client.post(
        "/v1/api-keys",
        json={"name": "Sneaky Key", "project_id": other_project.id},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_new_api_key_can_authenticate(client, auth_headers, tenant):
    create_response = await client.post(
        "/v1/api-keys", json={"name": "Usable Key"}, headers=auth_headers
    )
    new_raw_key = create_response.json()["key"]

    response = await client.get(
        f"/v1/organizations/{tenant['organization'].id}",
        headers={"Authorization": f"Bearer {new_raw_key}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_api_keys_never_exposes_raw_key_or_hash(client, auth_headers, tenant):
    await client.post("/v1/api-keys", json={"name": "Another Key"}, headers=auth_headers)

    response = await client.get("/v1/api-keys", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2  # the tenant fixture's own key + the new one
    for item in body["items"]:
        assert "key" not in item
        assert "key_hash" not in item
        assert "raw_key" not in item
        assert "key_prefix" in item


@pytest.mark.asyncio
async def test_revoke_api_key(client, auth_headers, tenant):
    create_response = await client.post(
        "/v1/api-keys", json={"name": "Revoke Me"}, headers=auth_headers
    )
    key_id = create_response.json()["id"]
    raw_key = create_response.json()["key"]

    revoke_response = await client.post(f"/v1/api-keys/{key_id}/revoke", headers=auth_headers)

    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"
    assert revoke_response.json()["revoked_at"] is not None

    auth_response = await client.get(
        f"/v1/organizations/{tenant['organization'].id}",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert auth_response.status_code == 401
    assert auth_response.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_revoke_foreign_organizations_key_is_not_found(client, auth_headers, db_session):
    from tests import factories

    other_org = await factories.create_organization(db_session, name="Other Org")
    other_key, _ = await factories.create_api_key(db_session, organization_id=other_org.id)
    await db_session.commit()

    response = await client.post(f"/v1/api-keys/{other_key.id}/revoke", headers=auth_headers)

    assert response.status_code == 404
