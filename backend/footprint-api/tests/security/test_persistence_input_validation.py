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
async def test_malformed_id_in_path_returns_not_found_not_server_error(client, auth_headers):
    for path in [
        "/v1/workloads/not-a-real-id-at-all",
        "/v1/estimates/drop-table-estimates",
        "/v1/projects/%27%20OR%20%271%27%3D%271",
    ]:
        response = await client.get(path, headers=auth_headers)
        assert response.status_code in (404, 422), path
        assert "Traceback" not in response.text


@pytest.mark.asyncio
async def test_invalid_timestamp_is_rejected(client, auth_headers, wired_model):
    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "timestamp": "not-a-timestamp"},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_activity_type_is_rejected(client, auth_headers, wired_model):
    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "activity_type": "not-a-real-activity"},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_project_id_is_rejected(client, auth_headers, wired_model):
    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "project_id": "proj_does_not_exist"},
        headers=auth_headers,
    )

    # A project-scoped key supplying a mismatched project_id is a scope
    # violation (403), distinct from an org-level key referencing a
    # project that truly does not exist anywhere (404) - either is an
    # acceptable rejection here, never a 200 or 500.
    assert response.status_code in (403, 404)


@pytest.mark.asyncio
async def test_malformed_json_body_returns_clean_error(client, auth_headers):
    response = await client.post(
        "/v1/events",
        content=b"{not valid json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert "Traceback" not in response.text


@pytest.mark.asyncio
async def test_negative_page_limit_is_rejected(client, auth_headers):
    response = await client.get("/v1/workloads?limit=-5", headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_pagination_cursor_is_rejected_cleanly(client, auth_headers):
    response = await client.get("/v1/workloads?cursor=not-a-real-cursor", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
