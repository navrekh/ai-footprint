import json

from aifootprint.models import BatchResult


def test_create_sends_workloads_list(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/batch-estimate",
        json={
            "batch_id": "batch_1",
            "total_workloads": 2,
            "successful_estimates": 1,
            "failed_estimates": 1,
            "aggregate_impact": {
                "energy": {
                    "status": "partial",
                    "min": 0.1,
                    "max": 0.2,
                    "unit": "Wh",
                    "total_workloads": 2,
                    "measured_workloads": 1,
                },
                "water": {
                    "status": "partial",
                    "min": 0.1,
                    "max": 0.2,
                    "unit": "mL",
                    "total_workloads": 2,
                    "measured_workloads": 1,
                },
                "carbon": {
                    "status": "partial",
                    "min": 0.01,
                    "max": 0.02,
                    "unit": "gCO2e",
                    "total_workloads": 2,
                    "measured_workloads": 1,
                },
            },
            "results": [
                {
                    "index": 0,
                    "status": "success",
                    "estimate": {
                        "estimate_id": "est_1",
                        "energy": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "Wh"},
                        "water": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "mL"},
                        "carbon": {"status": "ok", "min": 0.01, "max": 0.02, "unit": "gCO2e"},
                        "confidence": "medium",
                        "evidence_level": 3,
                        "accounting_boundary": "B",
                        "methodology_version": "0.1",
                        "assumptions": [],
                        "created_at": "2026-01-01T00:00:00Z",
                    },
                    "error": None,
                },
                {
                    "index": 1,
                    "status": "failed",
                    "estimate": None,
                    "error": {
                        "code": "MODEL_NOT_FOUND",
                        "message": "Model 'x' was not found for provider 'y'.",
                        "request_id": "req_1",
                    },
                },
            ],
        },
    )
    workloads = [
        {
            "provider": "openai",
            "model": "model-id",
            "modality": "text",
            "activity_type": "text_generation",
            "input_tokens": 100,
        },
        {
            "provider": "y",
            "model": "x",
            "modality": "text",
            "activity_type": "text_generation",
        },
    ]
    result = client.batch.create(workloads)

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"workloads": workloads}

    assert isinstance(result, BatchResult)
    assert result.total_workloads == 2
    assert result.successful_estimates == 1
    assert result.failed_estimates == 1
    # A single invalid workload never fails the whole batch - each
    # item's outcome is reported independently.
    assert result.results[0].status == "success"
    assert result.results[1].status == "failed"
    assert result.results[1].error.code == "MODEL_NOT_FOUND"
    assert result.results[1].estimate is None
