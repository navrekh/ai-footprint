import pytest


@pytest.mark.asyncio
async def test_estimate_with_full_methodology_returns_ok_ranges(
    client, auth_headers, wired_model
):
    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 2000,
        "output_tokens": 1000,
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["energy"]["status"] == "ok"
    assert body["energy"]["min"] == 0.01
    assert body["energy"]["max"] == 0.02
    assert body["water"]["status"] == "ok"
    assert body["carbon"]["status"] == "ok"
    assert body["confidence"] == "low"
    assert body["evidence_level"] == 6
    assert body["methodology_version"] == "TEST_ONLY-0.1"
    assert body["estimate_id"].startswith("est_")


@pytest.mark.asyncio
async def test_estimate_without_matching_factor_returns_insufficient_data(
    client, auth_headers, wired_model
):
    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_reasoning",
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["energy"]["status"] == "insufficient_data"
    assert body["energy"]["min"] is None
    assert body["water"]["status"] == "insufficient_data"
    assert body["carbon"]["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_estimate_does_not_persist_a_workload(client, auth_headers, wired_model, db_session):
    from sqlalchemy import select

    from app.models.workload import AIWorkload

    payload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    response = await client.post("/v1/estimate", json=payload, headers=auth_headers)
    assert response.status_code == 200

    result = await db_session.execute(select(AIWorkload))
    assert result.scalars().first() is None
