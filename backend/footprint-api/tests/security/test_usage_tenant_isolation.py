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
async def test_organization_a_usage_never_includes_organization_bs_workloads(
    client, db_session, wired_model
):
    org_a = await factories.create_organization(db_session, name="Org A")
    project_a = await factories.create_project(db_session, org_a.id)
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    await db_session.commit()

    await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_b}"}
    )

    response = await client.get(
        "/v1/usage/summary", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 200
    assert response.json()["workloads"]["total"] == 0


@pytest.mark.asyncio
async def test_project_scoped_key_usage_is_limited_to_its_own_project(
    client, db_session, tenant, auth_headers, wired_model
):
    other_project = await factories.create_project(db_session, tenant["organization"].id)
    _, other_raw_key = await factories.create_api_key(db_session, other_project.id)
    await db_session.commit()

    await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {other_raw_key}"}
    )
    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    response = await client.get("/v1/usage/summary", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["workloads"]["total"] == 1


@pytest.mark.asyncio
async def test_organization_level_key_aggregates_across_its_own_projects(
    client, db_session, wired_model
):
    org = await factories.create_organization(db_session)
    project_a = await factories.create_project(db_session, org.id, name="Project A")
    project_b = await factories.create_project(db_session, org.id, name="Project B")
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    _, org_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_a}"}
    )
    await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_b}"}
    )

    response = await client.get(
        "/v1/usage/summary", headers={"Authorization": f"Bearer {org_key}"}
    )

    assert response.status_code == 200
    assert response.json()["workloads"]["total"] == 2


@pytest.mark.asyncio
async def test_project_scoped_key_ignores_a_foreign_project_filter_and_stays_hard_scoped(
    client, db_session, auth_headers, wired_model
):
    """A project-scoped key can never see another project's data no
    matter what `project` filter it supplies - resolve_optional_project_filter
    hard-scopes it to the key's own project (the same rule already
    established for GET /v1/workloads), so an attempted foreign project
    filter is silently superseded rather than granting a peek at - or
    even confirming the existence of - another organization's project.
    """
    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    await db_session.commit()

    await client.post(
        "/v1/events",
        json={
            "provider": "openai",
            "model": "test-only-model",
            "modality": "text",
            "activity_type": "text_generation",
            "input_tokens": 10,
            "output_tokens": 10,
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/v1/usage/summary", params={"project": other_project.id}, headers=auth_headers
    )

    assert response.status_code == 200
    # Reflects the caller's own project (1 workload), never the foreign
    # project's data (which has none anyway - this proves scoping, not
    # just an empty coincidence).
    assert response.json()["workloads"]["total"] == 1


@pytest.mark.asyncio
async def test_organization_level_key_project_filter_never_leaks_a_foreign_organization(
    client, db_session
):
    """An organization-level key's project filter is passed through to
    the query, but the mandatory organization_id filter is always
    applied first - so a foreign organization's project_id can never
    match any row in the caller's own organization, and the result is
    safely empty rather than leaking or erroring in a way that would
    confirm the other project's existence.
    """
    org = await factories.create_organization(db_session)
    _, org_key = await factories.create_api_key(db_session, organization_id=org.id)

    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    await db_session.commit()

    response = await client.get(
        "/v1/usage/summary",
        params={"project": other_project.id},
        headers={"Authorization": f"Bearer {org_key}"},
    )

    assert response.status_code == 200
    assert response.json()["workloads"]["total"] == 0


@pytest.mark.asyncio
async def test_by_provider_usage_is_organization_scoped(client, db_session, wired_model):
    org_a = await factories.create_organization(db_session, name="Org A")
    project_a = await factories.create_project(db_session, org_a.id)
    _, raw_key_a = await factories.create_api_key(db_session, project_a.id)

    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    _, raw_key_b = await factories.create_api_key(db_session, project_b.id)
    await db_session.commit()

    await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key_b}"}
    )

    response = await client.get(
        "/v1/usage/by-provider", headers={"Authorization": f"Bearer {raw_key_a}"}
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_usage_endpoints_require_auth(client):
    for path in [
        "/v1/usage/summary",
        "/v1/usage/by-provider",
        "/v1/usage/by-model",
        "/v1/usage/by-activity",
        "/v1/usage/by-application",
        "/v1/usage/timeseries",
    ]:
        response = await client.get(path)
        assert response.status_code == 401, path
