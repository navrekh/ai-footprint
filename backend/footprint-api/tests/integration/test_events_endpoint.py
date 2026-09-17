import pytest
from sqlalchemy import select

from app.models.estimate import Estimate
from app.models.workload import AIWorkload


@pytest.mark.asyncio
async def test_event_is_persisted_with_estimate(client, auth_headers, wired_model, db_session):
    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 2000,
        "output_tokens": 1000,
    }

    response = await client.post("/v1/events", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"].startswith("evt_")
    assert body["estimate_id"].startswith("est_")

    workload = (
        await db_session.execute(select(AIWorkload).where(AIWorkload.id == body["event_id"]))
    ).scalar_one()
    assert workload.provider == "openai"
    assert workload.input_tokens == 2000

    estimate = (
        await db_session.execute(select(Estimate).where(Estimate.id == body["estimate_id"]))
    ).scalar_one()
    assert estimate.workload_id == workload.id
    assert estimate.energy_status == "ok"


@pytest.mark.asyncio
async def test_event_persists_even_when_methodology_is_unavailable(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(
        db_session, provider_id=provider.id, methodology_version=None
    )
    await db_session.commit()

    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    response = await client.post("/v1/events", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()

    estimate = (
        await db_session.execute(select(Estimate).where(Estimate.id == body["estimate_id"]))
    ).scalar_one()
    assert estimate.energy_status == "insufficient_data"
    assert estimate.methodology_version is None


@pytest.mark.asyncio
async def test_event_supports_parent_child_relationship(client, auth_headers, wired_model):
    parent_payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }
    parent_response = await client.post("/v1/events", json=parent_payload, headers=auth_headers)
    parent_id = parent_response.json()["event_id"]

    child_payload = {**parent_payload, "parent_workload_id": parent_id}
    child_response = await client.post("/v1/events", json=child_payload, headers=auth_headers)

    assert child_response.status_code == 200


@pytest.mark.asyncio
async def test_unknown_provider_returns_error_and_does_not_persist(
    client, auth_headers, db_session
):
    payload = {
        "provider": "does-not-exist",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
    }

    response = await client.post("/v1/events", json=payload, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROVIDER_NOT_FOUND"

    result = await db_session.execute(select(AIWorkload))
    assert result.scalars().first() is None
