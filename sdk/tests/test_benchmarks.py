import json

from aifootprint.models import BenchmarkDefinition, BenchmarkList, BenchmarkRunResult


def _definition(**overrides) -> dict:
    body = {
        "benchmark_id": "bm_1",
        "version": "1.0",
        "name": "Standard Chat Benchmark",
        "description": "A fixed prompt/response pair used for cross-provider comparison.",
        "activity_type": "text_generation",
        "modality": "text",
        "parameters": {"input_tokens": 2000, "output_tokens": 1000},
    }
    body.update(overrides)
    return body


def _run_result() -> dict:
    return {
        "benchmark_id": "bm_1",
        "benchmark_version": "1.0",
        "modality": "text",
        "activity_type": "text_generation",
        "results": [
            {
                "candidate": {"provider": "openai", "model": "m1", "model_version": None},
                "status": "success",
                "resolved": {"provider": "openai", "model": "m1", "model_version": "2026-01-01"},
                "estimate": {
                    "estimate_id": "est_1",
                    "energy": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "Wh"},
                    "water": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "mL"},
                    "carbon": {"status": "ok", "min": 0.01, "max": 0.02, "unit": "gCO2e"},
                    "confidence": "medium",
                    "evidence_level": 4,
                    "accounting_boundary": "A",
                    "methodology_version": "0.1",
                    "assumptions": [],
                    "created_at": "2026-01-01T00:00:00Z",
                },
                "normalized": None,
                "error": None,
            },
            {
                "candidate": {"provider": "anthropic", "model": "m2", "model_version": None},
                "status": "failed",
                "resolved": None,
                "estimate": None,
                "normalized": None,
                "error": {
                    "code": "MODEL_NOT_FOUND",
                    "message": "Model 'm2' was not found for provider 'anthropic'.",
                    "request_id": "req_1",
                },
            },
        ],
    }


def test_list_no_filters(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/benchmarks",
        json={"items": [_definition()], "total": 1},
    )
    result = client.benchmarks.list()
    assert isinstance(result, BenchmarkList)
    assert result.items[0].benchmark_id == "bm_1"


def test_list_with_filters(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/benchmarks?activity_type=text_generation&modality=text",
        json={"items": [_definition()], "total": 1},
    )
    result = client.benchmarks.list(activity_type="text_generation", modality="text")
    assert result.total == 1


def test_get_preserves_version_and_parameters(httpx_mock, client):
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/benchmarks/bm_1", json=_definition()
    )
    result = client.benchmarks.get("bm_1")
    assert isinstance(result, BenchmarkDefinition)
    assert result.version == "1.0"
    assert result.parameters == {"input_tokens": 2000, "output_tokens": 1000}


def test_run_sends_benchmark_id_and_candidates(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/benchmarks/run", json=_run_result()
    )
    candidates = [
        {"provider": "openai", "model": "m1"},
        {"provider": "anthropic", "model": "m2"},
    ]
    result = client.benchmarks.run("bm_1", candidates)

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"benchmark_id": "bm_1", "candidates": candidates}

    assert isinstance(result, BenchmarkRunResult)
    assert result.benchmark_version == "1.0"


def test_run_results_are_independent_per_candidate_not_ranked(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/benchmarks/run", json=_run_result()
    )
    result = client.benchmarks.run(
        "bm_1", [{"provider": "openai", "model": "m1"}, {"provider": "anthropic", "model": "m2"}]
    )
    assert result.results[0].status == "success"
    assert result.results[1].status == "failed"
    assert result.results[1].error.code == "MODEL_NOT_FOUND"
    for forbidden in ("winner", "best", "score", "rank", "ranking", "recommended"):
        assert not hasattr(result, forbidden)
        for item in result.results:
            assert not hasattr(item, forbidden)
