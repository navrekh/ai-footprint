import json

from aifootprint.models import CompareResult


def _estimate(**overrides) -> dict:
    body = {
        "estimate_id": "est_1",
        "energy": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "Wh"},
        "water": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "mL"},
        "carbon": {"status": "ok", "min": 0.01, "max": 0.02, "unit": "gCO2e"},
        "confidence": "low",
        "evidence_level": 6,
        "accounting_boundary": "A",
        "methodology_version": "TEST_ONLY-0.1",
        "assumptions": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def _compare_response() -> dict:
    return {
        "comparison_id": "cmp_1",
        "modality": "text",
        "activity_type": "text_generation",
        "results": [
            {
                "candidate": {"provider": "openai", "model": "m1", "model_version": None},
                "status": "success",
                "resolved": {"provider": "openai", "model": "m1", "model_version": "2026-01-01"},
                "estimate": _estimate(estimate_id="est_1"),
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


def test_create_sends_candidates_and_workload_fields(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )
    candidates = [
        {"provider": "openai", "model": "m1"},
        {"provider": "anthropic", "model": "m2"},
    ]
    result = client.compare.create(
        modality="text",
        activity_type="text_generation",
        input_tokens=2000,
        output_tokens=1000,
        candidates=candidates,
    )

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["candidates"] == candidates
    assert body["modality"] == "text"
    assert body["activity_type"] == "text_generation"
    # provider/model are never top-level fields on a compare request -
    # they belong exclusively to each candidate.
    assert "provider" not in body
    assert "model" not in body

    assert isinstance(result, CompareResult)
    assert len(result.results) == 2


def test_results_are_returned_in_the_exact_order_and_shape_provided(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )
    result = client.compare.create(
        modality="text",
        activity_type="text_generation",
        candidates=[
            {"provider": "openai", "model": "m1"},
            {"provider": "anthropic", "model": "m2"},
        ],
    )
    assert result.results[0].candidate.provider == "openai"
    assert result.results[0].status == "success"
    assert result.results[1].candidate.provider == "anthropic"
    assert result.results[1].status == "failed"
    assert result.results[1].error.code == "MODEL_NOT_FOUND"


def test_resolved_identity_differs_from_requested_candidate_when_model_version_omitted(
    httpx_mock, client
):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )
    result = client.compare.create(
        modality="text",
        activity_type="text_generation",
        candidates=[
            {"provider": "openai", "model": "m1"},
            {"provider": "anthropic", "model": "m2"},
        ],
    )
    first = result.results[0]
    assert first.candidate.model_version is None
    assert first.resolved.model_version == "2026-01-01"


def test_no_ranking_or_score_field_exists_anywhere_on_the_result(httpx_mock, client):
    """The SDK must never introduce ranking semantics - this asserts the
    actual model classes have no such attribute, not just that this one
    mocked response lacks one.
    """
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )
    result = client.compare.create(
        modality="text",
        activity_type="text_generation",
        candidates=[
            {"provider": "openai", "model": "m1"},
            {"provider": "anthropic", "model": "m2"},
        ],
    )
    for forbidden in ("winner", "best", "score", "rank", "ranking", "recommended"):
        assert not hasattr(result, forbidden)
        for item in result.results:
            assert not hasattr(item, forbidden)


def test_normalized_intensity_is_preserved_when_present(httpx_mock, client):
    response = _compare_response()
    response["results"][0]["normalized"] = {
        "denominator": {"value": 3.0, "unit": "1K tokens", "basis": "input_plus_output"},
        "energy": {
            "status": "ok",
            "min": 0.033,
            "max": 0.066,
            "unit": "Wh per 1K tokens",
            "confidence": "low",
            "evidence_level": 6,
            "methodology_version": "TEST_ONLY-0.1",
            "accounting_boundary": "A",
        },
        "water": None,
        "carbon": None,
    }
    httpx_mock.add_response(method="POST", url="http://testserver/v1/compare", json=response)
    result = client.compare.create(
        modality="text",
        activity_type="text_generation",
        candidates=[
            {"provider": "openai", "model": "m1"},
            {"provider": "anthropic", "model": "m2"},
        ],
    )
    normalized = result.results[0].normalized
    assert normalized.denominator.basis == "input_plus_output"
    assert normalized.energy.min == 0.033
    assert normalized.energy.max == 0.066
