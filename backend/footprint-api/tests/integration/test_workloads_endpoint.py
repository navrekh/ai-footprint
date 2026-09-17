import pytest

WORKLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 10,
    "output_tokens": 10,
}


@pytest.mark.asyncio
async def test_list_workloads_paginates_with_stable_ordering(client, auth_headers, wired_model):
    created_ids = []
    for _ in range(3):
        response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
        created_ids.append(response.json()["workload_id"])

    first_page = await client.get("/v1/workloads?limit=2", headers=auth_headers)
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_cursor"] is not None

    second_page = await client.get(
        f"/v1/workloads?limit=2&cursor={first_body['next_cursor']}", headers=auth_headers
    )
    second_body = second_page.json()
    assert len(second_body["items"]) == 1
    assert second_body["next_cursor"] is None

    all_returned_ids = {item["id"] for item in first_body["items"] + second_body["items"]}
    assert all_returned_ids == set(created_ids)


@pytest.mark.asyncio
async def test_list_workloads_rejects_excessive_limit(client, auth_headers, wired_model):
    response = await client.get("/v1/workloads?limit=500", headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_workloads_filters_by_activity_type(client, auth_headers, wired_model):
    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    await client.post(
        "/v1/events", json={**WORKLOAD, "activity_type": "text_reasoning"}, headers=auth_headers
    )

    response = await client.get(
        "/v1/workloads?activity_type=text_reasoning", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["activity_type"] == "text_reasoning"


@pytest.mark.asyncio
async def test_list_workloads_filters_by_timestamp_range(client, auth_headers, wired_model):
    await client.post(
        "/v1/events",
        json={**WORKLOAD, "timestamp": "2020-01-01T00:00:00Z"},
        headers=auth_headers,
    )
    await client.post(
        "/v1/events",
        json={**WORKLOAD, "timestamp": "2025-06-01T00:00:00Z"},
        headers=auth_headers,
    )

    response = await client.get(
        "/v1/workloads?from=2024-01-01T00:00:00Z&to=2026-01-01T00:00:00Z",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["timestamp"].startswith("2025-06-01")


@pytest.mark.asyncio
async def test_get_workload_by_id(client, auth_headers, wired_model):
    create_response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    workload_id = create_response.json()["workload_id"]

    response = await client.get(f"/v1/workloads/{workload_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == workload_id
    assert response.json()["provider"] == "openai"


@pytest.mark.asyncio
async def test_get_unknown_workload_returns_not_found(client, auth_headers):
    response = await client.get("/v1/workloads/evt_does_not_exist", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_scoped_key_only_sees_its_own_project(
    client, auth_headers, wired_model, db_session, tenant
):
    from tests import factories

    other_project = await factories.create_project(db_session, tenant["organization"].id)
    _, other_raw_key = await factories.create_api_key(db_session, other_project.id)
    await db_session.commit()

    await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {other_raw_key}"}
    )

    response = await client.get("/v1/workloads", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["project_id"] == tenant["project"].id
