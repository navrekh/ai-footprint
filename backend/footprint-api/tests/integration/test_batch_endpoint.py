import pytest


@pytest.mark.asyncio
async def test_batch_reports_success_and_failure_independently(
    client, auth_headers, wired_model
):
    payload = {
        "workloads": [
            {
                "provider": "openai",
                "model": "test-only-model",
                "modality": "text",
                "activity_type": "text_generation",
                "input_tokens": 100,
                "output_tokens": 50,
            },
            {
                "provider": "does-not-exist",
                "model": "test-only-model",
                "modality": "text",
                "activity_type": "text_generation",
            },
            {
                "provider": "openai",
                "model": "test-only-model",
                "modality": "text",
                "activity_type": "text_generation",
                "input_tokens": 200,
                "output_tokens": 100,
            },
        ]
    }

    response = await client.post("/v1/batch-estimate", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_workloads"] == 3
    assert body["successful_estimates"] == 2
    assert body["failed_estimates"] == 1
    assert body["results"][1]["status"] == "failed"
    assert body["results"][1]["error"]["code"] == "PROVIDER_NOT_FOUND"

    # Two successful workloads, each contributing the same 0.01-0.02 Wh range.
    assert body["aggregate_impact"]["energy"]["min"] == pytest.approx(0.02)
    assert body["aggregate_impact"]["energy"]["max"] == pytest.approx(0.04)
    assert body["aggregate_impact"]["energy"]["status"] == "ok"
    assert body["aggregate_impact"]["energy"]["total_workloads"] == 2
    assert body["aggregate_impact"]["energy"]["measured_workloads"] == 2


@pytest.mark.asyncio
async def test_batch_all_metrics_available_reports_ok_with_full_completeness(
    client, auth_headers, wired_model
):
    workload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    response = await client.post(
        "/v1/batch-estimate", json={"workloads": [workload, workload]}, headers=auth_headers
    )

    assert response.status_code == 200
    aggregate = response.json()["aggregate_impact"]
    for metric in ("energy", "water", "carbon"):
        assert aggregate[metric]["status"] == "ok"
        assert aggregate[metric]["total_workloads"] == 2
        assert aggregate[metric]["measured_workloads"] == 2


@pytest.mark.asyncio
async def test_batch_partial_metric_availability_is_reported_explicitly(
    client, auth_headers, wired_model, db_session
):
    from tests import factories

    # Only an energy factor exists for text_reasoning - water/carbon do not.
    await factories.create_factor(
        db_session,
        metric="energy",
        activity_type="text_reasoning",
        value_min=0.05,
        value_max=0.06,
    )
    await db_session.commit()

    full_workload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }
    energy_only_workload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_reasoning",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    response = await client.post(
        "/v1/batch-estimate",
        json={"workloads": [full_workload, energy_only_workload]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    aggregate = response.json()["aggregate_impact"]

    # Both workloads contributed an energy measurement.
    assert aggregate["energy"]["status"] == "ok"
    assert aggregate["energy"]["total_workloads"] == 2
    assert aggregate["energy"]["measured_workloads"] == 2

    # Only one of the two workloads contributed water/carbon - a partial
    # aggregate must never look like a complete one.
    assert aggregate["water"]["status"] == "partial"
    assert aggregate["water"]["total_workloads"] == 2
    assert aggregate["water"]["measured_workloads"] == 1
    assert aggregate["water"]["min"] == pytest.approx(0.02)
    assert aggregate["water"]["max"] == pytest.approx(0.03)

    assert aggregate["carbon"]["status"] == "partial"
    assert aggregate["carbon"]["measured_workloads"] == 1


@pytest.mark.asyncio
async def test_batch_all_workloads_unavailable_for_metric_is_insufficient_data(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(db_session, provider_id=provider.id)
    # Deliberately no factors seeded.
    await db_session.commit()

    workload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    response = await client.post(
        "/v1/batch-estimate", json={"workloads": [workload, workload]}, headers=auth_headers
    )

    assert response.status_code == 200
    aggregate = response.json()["aggregate_impact"]
    for metric in ("energy", "water", "carbon"):
        assert aggregate[metric]["status"] == "insufficient_data"
        assert aggregate[metric]["min"] is None
        assert aggregate[metric]["max"] is None
        assert aggregate[metric]["total_workloads"] == 2
        assert aggregate[metric]["measured_workloads"] == 0


@pytest.mark.asyncio
async def test_batch_exceeding_max_size_is_rejected(client, auth_headers, wired_model):
    from app.core.config import get_settings

    max_size = get_settings().MAX_BATCH_SIZE
    workload = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
        "input_tokens": 10,
        "output_tokens": 10,
    }

    response = await client.post(
        "/v1/batch-estimate",
        json={"workloads": [workload] * (max_size + 1)},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
