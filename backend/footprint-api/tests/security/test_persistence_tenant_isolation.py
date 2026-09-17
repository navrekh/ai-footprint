import pytest

from tests import factories

WORKLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 10,
    "output_tokens": 10,
}


@pytest.mark.asyncio
async def test_organization_a_cannot_access_organization_bs_project(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    _, raw_key_a = await factories.create_api_key(db_session, organization_id=org_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    await db_session.commit()

    response = await client.get(
        f"/v1/projects/{project_b.id}", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_organization_a_cannot_access_organization_bs_workloads(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    project_a = await factories.create_project(db_session, org_a.id)
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    await db_session.commit()

    create_response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_b}"}
    )
    workload_id = create_response.json()["workload_id"]

    response = await client.get(
        f"/v1/workloads/{workload_id}", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 404

    list_response = await client.get(
        "/v1/workloads", headers={"Authorization": f"Bearer {raw_key_a}"}
    )
    assert all(item["id"] != workload_id for item in list_response.json()["items"])


@pytest.mark.asyncio
async def test_organization_a_cannot_access_organization_bs_estimates(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    project_a = await factories.create_project(db_session, org_a.id)
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    await db_session.commit()

    create_response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_b}"}
    )
    estimate_id = create_response.json()["estimate_id"]

    response = await client.get(
        f"/v1/estimates/{estimate_id}", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_organization_a_cannot_revoke_organization_bs_api_key(client, db_session):
    org_a = await factories.create_organization(db_session, name="Org A")
    _, raw_key_a = await factories.create_api_key(db_session, organization_id=org_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    key_b, _ = await factories.create_api_key(db_session, organization_id=org_b.id)
    await db_session.commit()

    response = await client.post(
        f"/v1/api-keys/{key_b.id}/revoke", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 404

    await db_session.refresh(key_b)
    assert key_b.status == "active"


@pytest.mark.asyncio
async def test_organization_a_cannot_submit_events_into_organization_bs_project(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    _, raw_key_a = await factories.create_api_key(db_session, organization_id=org_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "project_id": project_b.id},
        headers={"Authorization": f"Bearer {raw_key_a}"},
    )

    assert response.status_code == 404
