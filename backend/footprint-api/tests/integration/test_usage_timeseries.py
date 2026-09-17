from datetime import UTC, datetime

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
async def test_timeseries_buckets_by_day(client, auth_headers, wired_model):
    day1 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC).isoformat()
    day2 = datetime(2026, 1, 2, 12, 0, tzinfo=UTC).isoformat()

    await client.post("/v1/events", json={**WORKLOAD, "timestamp": day1}, headers=auth_headers)
    await client.post("/v1/events", json={**WORKLOAD, "timestamp": day2}, headers=auth_headers)

    response = await client.get(
        "/v1/usage/timeseries"
        "?granularity=day&from=2026-01-01T00:00:00Z&to=2026-01-03T00:00:00Z",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["granularity"] == "day"
    assert len(body["items"]) == 2
    assert all(point["workloads"]["total"] == 1 for point in body["items"])


@pytest.mark.asyncio
async def test_timeseries_buckets_by_month(client, auth_headers, wired_model):
    jan = datetime(2026, 1, 15, tzinfo=UTC).isoformat()
    feb = datetime(2026, 2, 15, tzinfo=UTC).isoformat()

    await client.post("/v1/events", json={**WORKLOAD, "timestamp": jan}, headers=auth_headers)
    await client.post("/v1/events", json={**WORKLOAD, "timestamp": feb}, headers=auth_headers)

    response = await client.get(
        "/v1/usage/timeseries"
        "?granularity=month&from=2026-01-01T00:00:00Z&to=2026-03-01T00:00:00Z",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


@pytest.mark.asyncio
async def test_timeseries_rejects_excessively_wide_range_for_day_granularity(
    client, auth_headers
):
    from_ts = datetime(2000, 1, 1, tzinfo=UTC).isoformat()
    to_ts = datetime(2026, 1, 1, tzinfo=UTC).isoformat()

    response = await client.get(
        "/v1/usage/timeseries",
        params={"granularity": "day", "from": from_ts, "to": to_ts},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


@pytest.mark.asyncio
async def test_timeseries_invalid_granularity_is_rejected(client, auth_headers):
    response = await client.get(
        "/v1/usage/timeseries?granularity=fortnight", headers=auth_headers
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_timeseries_preserves_range_aggregation_within_bucket(
    client, auth_headers, wired_model
):
    ts = datetime(2026, 1, 1, 8, 0, tzinfo=UTC).isoformat()
    await client.post("/v1/events", json={**WORKLOAD, "timestamp": ts}, headers=auth_headers)
    await client.post("/v1/events", json={**WORKLOAD, "timestamp": ts}, headers=auth_headers)

    response = await client.get(
        "/v1/usage/timeseries"
        "?granularity=day&from=2026-01-01T00:00:00Z&to=2026-01-02T00:00:00Z",
        headers=auth_headers,
    )

    assert response.status_code == 200
    point = response.json()["items"][0]
    assert point["energy"]["min"] == pytest.approx(0.02)
    assert point["energy"]["max"] == pytest.approx(0.04)
