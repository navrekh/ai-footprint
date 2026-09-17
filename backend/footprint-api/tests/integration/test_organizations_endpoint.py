import pytest


@pytest.mark.asyncio
async def test_create_organization_bootstraps_project_and_key(client):
    response = await client.post("/v1/organizations", json={"name": "Acme AI"})

    assert response.status_code == 200
    body = response.json()
    assert body["organization"]["name"] == "Acme AI"
    assert body["organization"]["slug"]
    assert body["organization"]["status"] == "active"
    assert body["project"]["organization_id"] == body["organization"]["id"]
    assert body["project"]["name"] == "Default Project"
    assert body["api_key"]["key"].startswith("afp_test_")


@pytest.mark.asyncio
async def test_created_api_key_can_authenticate(client):
    create_response = await client.post("/v1/organizations", json={"name": "Bootstrap Co"})
    raw_key = create_response.json()["api_key"]["key"]
    org_id = create_response.json()["organization"]["id"]

    response = await client.get(
        f"/v1/organizations/{org_id}", headers={"Authorization": f"Bearer {raw_key}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == org_id


@pytest.mark.asyncio
async def test_get_organization_requires_auth(client):
    create_response = await client.post("/v1/organizations", json={"name": "No Auth Co"})
    org_id = create_response.json()["organization"]["id"]

    response = await client.get(f"/v1/organizations/{org_id}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_organization_rejects_cross_tenant_access(client):
    org_a_response = await client.post("/v1/organizations", json={"name": "Org A"})
    org_b_response = await client.post("/v1/organizations", json={"name": "Org B"})
    raw_key_a = org_a_response.json()["api_key"]["key"]
    org_b_id = org_b_response.json()["organization"]["id"]

    response = await client.get(
        f"/v1/organizations/{org_b_id}", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_duplicate_organization_names_get_distinct_slugs(client):
    first = await client.post("/v1/organizations", json={"name": "Duplicate Name"})
    second = await client.post("/v1/organizations", json={"name": "Duplicate Name"})

    assert first.json()["organization"]["slug"] != second.json()["organization"]["slug"]
