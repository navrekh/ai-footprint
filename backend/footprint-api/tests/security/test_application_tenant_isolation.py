import pytest

from tests import factories


@pytest.mark.asyncio
async def test_organization_a_cannot_access_organization_bs_application(client, db_session):
    org_a = await factories.create_organization(db_session, name="Org A")
    _, raw_key_a = await factories.create_api_key(db_session, organization_id=org_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    application_b = await factories.create_application(db_session, project_b.id)
    await db_session.commit()

    response = await client.get(
        f"/v1/applications/{application_b.id}",
        headers={"Authorization": f"Bearer {raw_key_a}"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_project_scoped_key_cannot_access_another_projects_application(
    client, db_session
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    application_b = await factories.create_application(db_session, project_b.id)
    await db_session.commit()

    response = await client.get(
        f"/v1/applications/{application_b.id}",
        headers={"Authorization": f"Bearer {raw_key_a}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_scoped_key_cannot_list_another_projects_applications(
    client, db_session
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    await factories.create_application(db_session, project_b.id)
    await db_session.commit()

    response = await client.get(
        "/v1/applications", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_organization_level_key_can_access_applications_across_its_projects(
    client, db_session
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    application_a = await factories.create_application(db_session, project_a.id)
    application_b = await factories.create_application(db_session, project_b.id)
    _, org_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {org_key}"}
    response_a = await client.get(f"/v1/applications/{application_a.id}", headers=headers)
    response_b = await client.get(f"/v1/applications/{application_b.id}", headers=headers)

    assert response_a.status_code == 200
    assert response_b.status_code == 200


@pytest.mark.asyncio
async def test_project_scoped_key_cannot_update_another_projects_application(
    client, db_session
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    application_b = await factories.create_application(db_session, project_b.id)
    await db_session.commit()

    response = await client.patch(
        f"/v1/applications/{application_b.id}",
        json={"description": "hijacked"},
        headers={"Authorization": f"Bearer {raw_key_a}"},
    )

    assert response.status_code == 404
