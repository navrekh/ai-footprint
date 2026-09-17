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
async def test_usage_by_provider_groups_correctly(client, auth_headers, wired_model):
    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    response = await client.get("/v1/usage/by-provider", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["provider"] == "openai"
    assert body["items"][0]["workloads"]["total"] == 2
    assert body["items"][0]["energy"]["min"] == pytest.approx(0.02)


@pytest.mark.asyncio
async def test_usage_by_model_includes_model_version(client, auth_headers, db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(
        db_session, provider_id=provider.id, name="test-only-model", version="v2"
    )
    await factories.create_factor(db_session, metric="energy")
    await factories.create_factor(db_session, metric="water")
    await factories.create_factor(db_session, metric="carbon")
    await db_session.commit()

    await client.post(
        "/v1/events",
        json={**WORKLOAD, "model_version": "v2"},
        headers=auth_headers,
    )

    response = await client.get("/v1/usage/by-model", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["provider"] == "openai"
    assert body["items"][0]["model"] == "test-only-model"
    assert body["items"][0]["model_version"] == "v2"


@pytest.mark.asyncio
async def test_usage_by_activity_groups_correctly(client, auth_headers, wired_model, db_session):
    await factories.create_factor(db_session, metric="energy", activity_type="text_reasoning")
    await db_session.commit()

    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    await client.post(
        "/v1/events", json={**WORKLOAD, "activity_type": "text_reasoning"}, headers=auth_headers
    )

    response = await client.get("/v1/usage/by-activity", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    activity_types = {item["activity_type"] for item in body["items"]}
    assert activity_types == {"text_generation", "text_reasoning"}


@pytest.mark.asyncio
async def test_usage_by_application_excludes_unassigned_workloads(
    client, auth_headers, tenant, wired_model, db_session
):
    application = await factories.create_application(db_session, tenant["project"].id)
    await db_session.commit()

    await client.post(
        "/v1/events", json={**WORKLOAD, "application_id": application.id}, headers=auth_headers
    )
    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)  # no application

    response = await client.get("/v1/usage/by-application", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["application_id"] == application.id
    assert body["items"][0]["project_id"] == tenant["project"].id
    assert body["items"][0]["workloads"]["total"] == 1


@pytest.mark.asyncio
async def test_usage_by_application_never_leaks_across_projects(
    client, auth_headers, tenant, wired_model, db_session
):
    other_project = await factories.create_project(db_session, tenant["organization"].id)
    other_application = await factories.create_application(db_session, other_project.id)
    _, other_raw_key = await factories.create_api_key(db_session, other_project.id)
    await db_session.commit()

    await client.post(
        "/v1/events",
        json={**WORKLOAD, "application_id": other_application.id},
        headers={"Authorization": f"Bearer {other_raw_key}"},
    )

    response = await client.get("/v1/usage/by-application", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_usage_by_application_filter_rejects_foreign_application(
    client, auth_headers, db_session
):
    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    other_application = await factories.create_application(db_session, other_project.id)
    await db_session.commit()

    response = await client.get(
        f"/v1/usage/summary?application={other_application.id}", headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_usage_breakdown_pagination(client, auth_headers, db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    for i in range(3):
        model_name = f"model-{i}"
        await factories.create_model(db_session, provider_id=provider.id, name=model_name)
        await factories.create_factor(db_session, metric="energy", model=model_name)
        await factories.create_factor(db_session, metric="water", model=model_name)
        await factories.create_factor(db_session, metric="carbon", model=model_name)
    await db_session.commit()

    for i in range(3):
        payload = {**WORKLOAD, "model": f"model-{i}"}
        response = await client.post("/v1/events", json=payload, headers=auth_headers)
        assert response.status_code == 200

    full_response = await client.get("/v1/usage/by-model", headers=auth_headers)
    assert full_response.status_code == 200
    assert full_response.json()["total"] == 3
    assert len(full_response.json()["items"]) == 3

    page_response = await client.get("/v1/usage/by-model?limit=1&offset=0", headers=auth_headers)
    assert page_response.status_code == 200
    assert page_response.json()["total"] == 3
    assert len(page_response.json()["items"]) == 1

    second_page = await client.get("/v1/usage/by-model?limit=1&offset=1", headers=auth_headers)
    assert len(second_page.json()["items"]) == 1
    assert page_response.json()["items"][0] != second_page.json()["items"][0]
