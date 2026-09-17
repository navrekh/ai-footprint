import pytest

from tests import factories

BASE_REQUEST = {
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 500,
    "output_tokens": 500,
}


@pytest.mark.asyncio
async def test_compare_missing_api_key_is_rejected(client):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_compare_invalid_api_key_is_rejected(client):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post(
        "/v1/compare", json=payload, headers={"Authorization": "Bearer not-a-real-key"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_compare_valid_api_key_succeeds(client, auth_headers, wired_model):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_benchmark_run_missing_api_key_is_rejected(client):
    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_benchmark_run_invalid_api_key_is_rejected(client):
    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post(
        "/v1/benchmarks/run", json=payload, headers={"Authorization": "Bearer not-a-real-key"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_benchmark_get_endpoints_succeed_with_no_authorization_header_at_all(client):
    """Proves GET /v1/benchmarks* are genuinely public reference-data
    endpoints (like GET /v1/providers, /v1/models, /v1/methodology) -
    not merely tolerant of a missing/bad key.
    """
    list_response = await client.get("/v1/benchmarks")
    detail_response = await client.get("/v1/benchmarks/text_generation_standard")

    assert "authorization" not in list_response.request.headers
    assert "authorization" not in detail_response.request.headers
    assert list_response.status_code == 200
    assert detail_response.status_code == 200


@pytest.mark.asyncio
async def test_compare_response_contains_no_tenant_fields(client, auth_headers, wired_model):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    raw_text = response.text.lower()
    for forbidden in ["organization_id", "project_id", "application_id", "api_key"]:
        assert forbidden not in raw_text


@pytest.mark.asyncio
async def test_benchmark_run_response_contains_no_tenant_fields(client, auth_headers, wired_model):
    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)

    raw_text = response.text.lower()
    for forbidden in ["organization_id", "project_id", "application_id", "api_key"]:
        assert forbidden not in raw_text


@pytest.mark.asyncio
async def test_compare_ignores_organization_and_project_id_in_request_body(
    client, auth_headers, wired_model, db_session
):
    """organization_id/project_id are not accepted as authoritative
    request fields at all - CompareRequest has no such fields, so
    supplying them must be silently ignored by Pydantic's default
    "extra fields ignored" behavior, never trusted or reflected back.
    """
    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    await db_session.commit()

    payload = {
        **BASE_REQUEST,
        "organization_id": other_org.id,
        "project_id": other_project.id,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    assert response.status_code == 200
    assert other_org.id not in response.text
    assert other_project.id not in response.text


@pytest.mark.asyncio
async def test_compare_does_not_read_or_write_any_workload_row(
    client, auth_headers, wired_model, db_session
):
    from sqlalchemy import select

    from app.models.workload import AIWorkload

    payload = {
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 500,
        "output_tokens": 500,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    await client.post("/v1/compare", json=payload, headers=auth_headers)

    result = await db_session.execute(select(AIWorkload))
    assert result.scalars().first() is None
