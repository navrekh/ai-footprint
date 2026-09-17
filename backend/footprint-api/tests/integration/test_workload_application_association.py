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
async def test_event_with_valid_application_persists_association(
    client, auth_headers, tenant, db_session, wired_model
):
    application = await factories.create_application(db_session, tenant["project"].id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "application_id": application.id},
        headers=auth_headers,
    )

    assert response.status_code == 200
    workload_id = response.json()["workload_id"]

    get_response = await client.get(f"/v1/workloads/{workload_id}", headers=auth_headers)
    assert get_response.json()["application_id"] == application.id


@pytest.mark.asyncio
async def test_event_without_application_remains_backward_compatible(
    client, auth_headers, wired_model
):
    response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    assert response.status_code == 200
    workload_id = response.json()["workload_id"]

    get_response = await client.get(f"/v1/workloads/{workload_id}", headers=auth_headers)
    assert get_response.json()["application_id"] is None


@pytest.mark.asyncio
async def test_event_with_application_from_different_project_is_rejected(
    client, auth_headers, tenant, db_session, wired_model
):
    other_project = await factories.create_project(db_session, tenant["organization"].id)
    other_application = await factories.create_application(db_session, other_project.id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "application_id": other_application.id},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "APPLICATION_PROJECT_MISMATCH"


@pytest.mark.asyncio
async def test_event_with_application_from_different_organization_is_not_found(
    client, auth_headers, wired_model, db_session
):
    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    other_application = await factories.create_application(db_session, other_project.id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "application_id": other_application.id},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPLICATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_event_with_nonexistent_application_id_is_not_found(
    client, auth_headers, wired_model
):
    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "application_id": "app_totally_made_up"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPLICATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_event_does_not_persist_when_application_is_invalid(
    client, auth_headers, wired_model, db_session
):
    from sqlalchemy import select

    from app.models.workload import AIWorkload

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "application_id": "app_totally_made_up"},
        headers=auth_headers,
    )
    assert response.status_code == 404

    result = await db_session.execute(select(AIWorkload))
    assert result.scalars().first() is None
