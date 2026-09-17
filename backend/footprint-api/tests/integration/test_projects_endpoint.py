import pytest


@pytest.mark.asyncio
async def test_create_and_get_project(client, auth_headers, tenant):
    create_response = await client.post(
        "/v1/projects",
        json={"name": "New Project", "description": "A test project"},
        headers=auth_headers,
    )

    assert create_response.status_code == 200
    body = create_response.json()
    assert body["organization_id"] == tenant["organization"].id
    assert body["name"] == "New Project"
    assert body["description"] == "A test project"
    assert body["status"] == "active"

    get_response = await client.get(f"/v1/projects/{body['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


@pytest.mark.asyncio
async def test_list_projects_returns_only_own_organization(client, auth_headers, tenant):
    await client.post("/v1/projects", json={"name": "Project 1"}, headers=auth_headers)
    await client.post("/v1/projects", json={"name": "Project 2"}, headers=auth_headers)

    response = await client.get("/v1/projects", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    # tenant fixture already created one project, plus the two above.
    assert body["total"] == 3
    assert all(p["organization_id"] == tenant["organization"].id for p in body["items"])


@pytest.mark.asyncio
async def test_update_project(client, auth_headers, tenant):
    create_response = await client.post(
        "/v1/projects", json={"name": "Mutable Project"}, headers=auth_headers
    )
    project_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/v1/projects/{project_id}",
        json={"description": "Updated", "status": "archived"},
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["description"] == "Updated"
    assert body["status"] == "archived"
    assert body["name"] == "Mutable Project"


@pytest.mark.asyncio
async def test_get_unknown_project_returns_not_found(client, auth_headers):
    response = await client.get("/v1/projects/proj_does_not_exist", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_project_endpoints_require_auth(client):
    response = await client.get("/v1/projects")

    assert response.status_code == 401
