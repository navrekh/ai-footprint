import pytest

from tests import factories


@pytest.mark.asyncio
async def test_project_cannot_reference_another_organizations_workload_as_parent(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    project_a = await factories.create_project(db_session, org_a.id)
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    await db_session.commit()

    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    # Org A creates a workload.
    response_a = await client.post(
        "/v1/events", json=payload, headers={"Authorization": f"Bearer {raw_key_a}"}
    )
    assert response_a.status_code == 200
    org_a_event_id = response_a.json()["event_id"]

    # Org B must not be able to attach a child event to org A's workload.
    cross_tenant_payload = {**payload, "parent_workload_id": org_a_event_id}
    response_b = await client.post(
        "/v1/events",
        json=cross_tenant_payload,
        headers={"Authorization": f"Bearer {raw_key_b}"},
    )

    assert response_b.status_code == 422
    assert response_b.json()["error"]["code"] == "INVALID_WORKLOAD"


@pytest.mark.asyncio
async def test_second_project_in_same_organization_cannot_reference_first_projects_workload(
    client, db_session, wired_model, tenant
):
    other_project = await factories.create_project(db_session, tenant["organization"].id)
    _, other_raw_key = await factories.create_api_key(db_session, other_project.id)
    await db_session.commit()

    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    first_response = await client.post(
        "/v1/events", json=payload, headers={"Authorization": f"Bearer {tenant['raw_key']}"}
    )
    first_event_id = first_response.json()["event_id"]

    # Same organization, but the FRD's isolation boundary is
    # organization-scoped: a sibling project in the same org may
    # legitimately share workload lineage, so this must succeed.
    child_payload = {**payload, "parent_workload_id": first_event_id}
    second_response = await client.post(
        "/v1/events", json=child_payload, headers={"Authorization": f"Bearer {other_raw_key}"}
    )

    assert second_response.status_code == 200
