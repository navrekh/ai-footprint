import pytest


@pytest.mark.asyncio
async def test_create_and_get_application(client, auth_headers, tenant):
    create_response = await client.post(
        "/v1/applications",
        json={
            "name": "Customer Support AI",
            "description": "Support bot",
            "environment": "production",
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 200
    body = create_response.json()
    assert body["project_id"] == tenant["project"].id
    assert body["name"] == "Customer Support AI"
    assert body["slug"] == "customer-support-ai"
    assert body["status"] == "active"
    assert body["environment"] == "production"

    get_response = await client.get(f"/v1/applications/{body['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


@pytest.mark.asyncio
async def test_create_application_without_environment(client, auth_headers):
    response = await client.post(
        "/v1/applications", json={"name": "Internal Copilot"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["environment"] is None
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_list_applications_returns_only_own_project(client, auth_headers, tenant):
    await client.post("/v1/applications", json={"name": "App 1"}, headers=auth_headers)
    await client.post("/v1/applications", json={"name": "App 2"}, headers=auth_headers)

    response = await client.get("/v1/applications", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(a["project_id"] == tenant["project"].id for a in body["items"])


@pytest.mark.asyncio
async def test_update_application(client, auth_headers):
    create_response = await client.post(
        "/v1/applications", json={"name": "Mutable App"}, headers=auth_headers
    )
    application_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/v1/applications/{application_id}",
        json={"description": "Updated", "status": "inactive", "environment": "staging"},
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["description"] == "Updated"
    assert body["status"] == "inactive"
    assert body["environment"] == "staging"
    assert body["name"] == "Mutable App"


@pytest.mark.asyncio
async def test_deactivating_application_does_not_delete_it(client, auth_headers):
    create_response = await client.post(
        "/v1/applications", json={"name": "Deactivate Me"}, headers=auth_headers
    )
    application_id = create_response.json()["id"]

    await client.patch(
        f"/v1/applications/{application_id}", json={"status": "inactive"}, headers=auth_headers
    )

    get_response = await client.get(f"/v1/applications/{application_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "inactive"


@pytest.mark.asyncio
async def test_get_unknown_application_returns_not_found(client, auth_headers):
    response = await client.get("/v1/applications/app_does_not_exist", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_application_endpoints_require_auth(client):
    response = await client.get("/v1/applications")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_organization_level_key_creates_application_with_explicit_project(
    client, db_session
):
    from tests import factories

    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    _, raw_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    response = await client.post(
        "/v1/applications",
        json={"name": "Org Level App", "project_id": project.id},
        headers={"Authorization": f"Bearer {raw_key}"},
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == project.id


@pytest.mark.asyncio
async def test_organization_level_key_without_project_id_is_rejected(client, db_session):
    from tests import factories

    org = await factories.create_organization(db_session)
    _, raw_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    response = await client.post(
        "/v1/applications",
        json={"name": "No Project App"},
        headers={"Authorization": f"Bearer {raw_key}"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_PARAMETER"
