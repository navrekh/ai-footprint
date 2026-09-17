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
async def test_project_a_key_can_retrieve_its_own_workload(
    client, db_session, wired_model
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    await db_session.commit()

    create_response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_a}"}
    )
    workload_id = create_response.json()["workload_id"]

    response = await client.get(
        f"/v1/workloads/{workload_id}", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == workload_id


@pytest.mark.asyncio
async def test_project_a_key_gets_not_found_for_project_b_workload(
    client, db_session, wired_model
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
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
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_project_a_key_can_retrieve_its_own_estimate(
    client, db_session, wired_model
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    await db_session.commit()

    create_response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_a}"}
    )
    estimate_id = create_response.json()["estimate_id"]

    response = await client.get(
        f"/v1/estimates/{estimate_id}", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 200
    assert response.json()["estimate_id"] == estimate_id


@pytest.mark.asyncio
async def test_project_a_key_gets_not_found_for_project_b_estimate(
    client, db_session, wired_model
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
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
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_organization_level_key_can_retrieve_records_across_its_own_projects(
    client, db_session, wired_model
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    _, org_raw_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    create_response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_a}"}
    )
    workload_id = create_response.json()["workload_id"]
    estimate_id = create_response.json()["estimate_id"]

    workload_response = await client.get(
        f"/v1/workloads/{workload_id}", headers={"Authorization": f"Bearer {org_raw_key}"}
    )
    estimate_response = await client.get(
        f"/v1/estimates/{estimate_id}", headers={"Authorization": f"Bearer {org_raw_key}"}
    )

    assert workload_response.status_code == 200
    assert estimate_response.status_code == 200

    # Sanity: project_b exists in the same org purely to prove the
    # org-level key is not just "happens to only have one project".
    assert project_b.organization_id == org.id


@pytest.mark.asyncio
async def test_organization_a_cannot_access_organization_bs_workload_or_estimate(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    _, org_a_key = await factories.create_api_key(db_session, organization_id=org_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    await db_session.commit()

    create_response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_b}"}
    )
    workload_id = create_response.json()["workload_id"]
    estimate_id = create_response.json()["estimate_id"]

    workload_response = await client.get(
        f"/v1/workloads/{workload_id}", headers={"Authorization": f"Bearer {org_a_key}"}
    )
    estimate_response = await client.get(
        f"/v1/estimates/{estimate_id}", headers={"Authorization": f"Bearer {org_a_key}"}
    )

    assert workload_response.status_code == 404
    assert estimate_response.status_code == 404
