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
