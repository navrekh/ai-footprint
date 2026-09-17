from datetime import UTC, datetime, timedelta

import pytest

from tests import factories

FULL_WORKLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 10,
    "output_tokens": 10,
}


@pytest.mark.asyncio
async def test_usage_summary_with_no_workloads_reports_zero_with_explicit_status(
    client, auth_headers
):
    response = await client.get("/v1/usage/summary", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["workloads"]["total"] == 0
    assert body["workloads"]["measured"] == 0
    assert body["workloads"]["coverage_percent"] == 0.0
    assert body["energy"]["status"] == "insufficient_data"
    assert body["energy"]["min"] is None
    assert body["energy"]["max"] is None


@pytest.mark.asyncio
async def test_usage_summary_fully_measured_reports_ok(client, auth_headers, wired_model):
    await client.post("/v1/events", json=FULL_WORKLOAD, headers=auth_headers)
    await client.post("/v1/events", json=FULL_WORKLOAD, headers=auth_headers)

    response = await client.get("/v1/usage/summary", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["workloads"]["total"] == 2
    assert body["workloads"]["measured"] == 2
    assert body["workloads"]["partial"] == 0
    assert body["workloads"]["insufficient_data"] == 0
    assert body["workloads"]["coverage_percent"] == 100.0
    assert body["energy"]["status"] == "ok"
    assert body["energy"]["min"] == pytest.approx(0.02)
    assert body["energy"]["max"] == pytest.approx(0.04)


@pytest.mark.asyncio
async def test_usage_summary_mixed_coverage_reports_partial(
    client, auth_headers, wired_model, db_session
):
    # Energy-only factor for text_reasoning - water/carbon stay insufficient.
    await factories.create_factor(
        db_session, metric="energy", activity_type="text_reasoning", value_min=0.05, value_max=0.06
    )
    await db_session.commit()

    await client.post("/v1/events", json=FULL_WORKLOAD, headers=auth_headers)
    await client.post(
        "/v1/events",
        json={**FULL_WORKLOAD, "activity_type": "text_reasoning"},
        headers=auth_headers,
    )

    response = await client.get("/v1/usage/summary", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["workloads"]["total"] == 2
    assert body["workloads"]["measured"] == 1
    assert body["workloads"]["partial"] == 1
    assert body["workloads"]["coverage_percent"] == 50.0
    assert body["energy"]["status"] == "ok"  # both workloads measured energy
    assert body["water"]["status"] == "partial"  # only one measured water


@pytest.mark.asyncio
async def test_usage_summary_no_measurable_data_reports_insufficient_data(
    client, auth_headers, db_session
):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(db_session, provider_id=provider.id)
    # No factors seeded at all.
    await db_session.commit()

    await client.post("/v1/events", json=FULL_WORKLOAD, headers=auth_headers)

    response = await client.get("/v1/usage/summary", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["workloads"]["total"] == 1
    assert body["workloads"]["insufficient_data"] == 1
    assert body["workloads"]["coverage_percent"] == 0.0
    assert body["energy"]["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_usage_summary_filters_by_date_range(client, auth_headers, wired_model):
    old_ts = (datetime.now(UTC) - timedelta(days=60)).isoformat()
    recent_ts = datetime.now(UTC).isoformat()

    await client.post(
        "/v1/events", json={**FULL_WORKLOAD, "timestamp": old_ts}, headers=auth_headers
    )
    await client.post(
        "/v1/events", json={**FULL_WORKLOAD, "timestamp": recent_ts}, headers=auth_headers
    )

    from_ts = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = await client.get(
        "/v1/usage/summary", params={"from": from_ts}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["workloads"]["total"] == 1


@pytest.mark.asyncio
async def test_usage_summary_invalid_date_range_is_rejected(client, auth_headers):
    response = await client.get(
        "/v1/usage/summary?from=2026-06-01T00:00:00Z&to=2026-01-01T00:00:00Z",
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


@pytest.mark.asyncio
async def test_usage_summary_requires_auth(client):
    response = await client.get("/v1/usage/summary")

    assert response.status_code == 401
