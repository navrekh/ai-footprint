import pytest

WORKLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 100,
    "output_tokens": 50,
}


@pytest.mark.asyncio
async def test_event_response_includes_workload_id_and_status(
    client, auth_headers, wired_model
):
    response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["workload_id"] == body["event_id"]
    assert body["status"] == "measured"
    assert body["idempotent_replay"] is False


@pytest.mark.asyncio
async def test_event_status_is_partial_when_only_some_metrics_measured(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(db_session, provider_id=provider.id)
    await factories.create_factor(db_session, metric="energy")
    await db_session.commit()

    response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "partial"


@pytest.mark.asyncio
async def test_event_status_is_insufficient_data_with_no_factors(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(db_session, provider_id=provider.id)
    await db_session.commit()

    response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_idempotency_key_replay_returns_same_ids_without_duplicating(
    client, auth_headers, wired_model
):
    payload = {**WORKLOAD, "idempotency_key": "order-123"}

    first = await client.post("/v1/events", json=payload, headers=auth_headers)
    second = await client.post("/v1/events", json=payload, headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["workload_id"] == second.json()["workload_id"]
    assert first.json()["estimate_id"] == second.json()["estimate_id"]
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True


@pytest.mark.asyncio
async def test_different_idempotency_keys_create_distinct_workloads(
    client, auth_headers, wired_model
):
    first = await client.post(
        "/v1/events", json={**WORKLOAD, "idempotency_key": "key-a"}, headers=auth_headers
    )
    second = await client.post(
        "/v1/events", json={**WORKLOAD, "idempotency_key": "key-b"}, headers=auth_headers
    )

    assert first.json()["workload_id"] != second.json()["workload_id"]


@pytest.mark.asyncio
async def test_org_level_key_must_supply_project_id(client, db_session, wired_model):
    from tests import factories

    org = await factories.create_organization(db_session, name="Org Level Org")
    _, raw_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    response = await client.post(
        "/v1/events", json=WORKLOAD, headers={"Authorization": f"Bearer {raw_key}"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_PARAMETER"


@pytest.mark.asyncio
async def test_org_level_key_with_explicit_project_id_succeeds(
    client, db_session, wired_model
):
    from tests import factories

    org = await factories.create_organization(db_session, name="Org Level Org 2")
    project = await factories.create_project(db_session, org.id)
    _, raw_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "project_id": project.id},
        headers={"Authorization": f"Bearer {raw_key}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_project_scoped_key_cannot_target_a_different_project(
    client, auth_headers, db_session, tenant, wired_model
):
    from tests import factories

    other_project = await factories.create_project(db_session, tenant["organization"].id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "project_id": other_project.id},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_persisted_workload_stores_model_version_and_new_fields(
    client, auth_headers, wired_model, db_session
):
    from sqlalchemy import select

    from app.models.workload import AIWorkload

    payload = {
        **WORKLOAD,
        "input_characters": 400,
        "output_characters": 200,
        "duration_ms": 1234.5,
    }

    response = await client.post("/v1/events", json=payload, headers=auth_headers)
    workload_id = response.json()["workload_id"]

    workload = (
        await db_session.execute(select(AIWorkload).where(AIWorkload.id == workload_id))
    ).scalar_one()
    assert workload.model_version == wired_model["model"].version
    assert workload.input_characters == 400
    assert workload.output_characters == 200
    assert workload.duration_ms == 1234.5


@pytest.mark.asyncio
async def test_persisted_estimate_stores_provenance(
    client, auth_headers, wired_model, db_session
):
    from sqlalchemy import select

    from app.models.estimate import Estimate

    response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    estimate_id = response.json()["estimate_id"]

    estimate = (
        await db_session.execute(select(Estimate).where(Estimate.id == estimate_id))
    ).scalar_one()
    assert estimate.provider == "openai"
    assert estimate.model == "test-only-model"
