import pytest

BASE_REQUEST = {
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 500,
    "output_tokens": 500,
}


@pytest.mark.asyncio
async def test_compare_two_candidates_both_successful(client, auth_headers, wired_model):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    for item in body["results"]:
        assert item["status"] == "success"
        assert item["estimate"]["energy"]["status"] == "ok"
        assert item["estimate"]["energy"]["min"] == pytest.approx(0.01)
        assert item["estimate"]["energy"]["max"] == pytest.approx(0.02)


@pytest.mark.asyncio
async def test_compare_candidates_are_never_aggregated(client, auth_headers, wired_model):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    body = response.json()
    first, second = body["results"]
    # Each candidate reports its own independent range - never a sum or
    # average across candidates.
    assert first["estimate"]["energy"]["min"] == second["estimate"]["energy"]["min"]
    assert first["estimate"]["energy"]["min"] == pytest.approx(0.01)


@pytest.mark.asyncio
async def test_compare_response_never_contains_ranking_or_score_fields(
    client, auth_headers, wired_model
):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    raw_text = response.text.lower()
    forbidden_terms = [
        "winner",
        "loser",
        "best_model",
        "recommended_model",
        "cheapest",
        "lowest_carbon",
        "lowest_energy",
        "ranking",
        '"score"',
        "overall_score",
    ]
    for term in forbidden_terms:
        assert term not in raw_text, f"forbidden ranking/score term found: {term}"


@pytest.mark.asyncio
async def test_compare_unknown_provider_is_isolated_to_that_candidate(
    client, auth_headers, wired_model
):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "does-not-exist", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    first, second = body["results"]
    assert first["status"] == "success"
    assert second["status"] == "failed"
    assert second["error"]["code"] == "PROVIDER_NOT_FOUND"
    assert second["estimate"] is None


@pytest.mark.asyncio
async def test_compare_unknown_model_is_isolated_to_that_candidate(
    client, auth_headers, wired_model
):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "does-not-exist-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    body = response.json()
    assert body["results"][1]["status"] == "failed"
    assert body["results"][1]["error"]["code"] == "MODEL_NOT_FOUND"


@pytest.mark.asyncio
async def test_compare_unsupported_modality_for_model_is_isolated_to_that_candidate(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text", "image"])
    await factories.create_methodology(db_session)
    await factories.create_model(
        db_session, provider_id=provider.id, name="text-only-model", modalities=["text"]
    )
    await db_session.commit()

    payload = {
        "modality": "image",
        "activity_type": "image_generation",
        "image_count": 1,
        "candidates": [
            {"provider": "openai", "model": "text-only-model"},
            {"provider": "openai", "model": "text-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    body = response.json()
    for item in body["results"]:
        assert item["status"] == "failed"
        assert item["error"]["code"] == "MODEL_NOT_SUPPORTED"


@pytest.mark.asyncio
async def test_compare_insufficient_methodology_is_preserved_not_fabricated(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(db_session, provider_id=provider.id, name="no-factor-model")
    # No factors seeded - insufficient_data is the only correct outcome.
    await db_session.commit()

    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "no-factor-model"},
            {"provider": "openai", "model": "no-factor-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    body = response.json()
    for item in body["results"]:
        assert item["status"] == "success"
        assert item["estimate"]["energy"]["status"] == "insufficient_data"
        assert item["estimate"]["energy"]["min"] is None
        assert item["estimate"]["energy"]["max"] is None


@pytest.mark.asyncio
async def test_compare_mixed_success_and_failure_candidates(client, auth_headers, wired_model):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "does-not-exist"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    body = response.json()
    statuses = [item["status"] for item in body["results"]]
    assert statuses == ["success", "failed", "success"]


@pytest.mark.asyncio
async def test_compare_preserves_confidence_and_methodology_version_per_candidate(
    client, auth_headers, wired_model
):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    estimate = response.json()["results"][0]["estimate"]
    assert estimate["confidence"] == "low"
    assert estimate["methodology_version"] is not None
    assert estimate["assumptions"]


@pytest.mark.asyncio
async def test_compare_includes_normalized_intensity_for_token_workload(
    client, auth_headers, wired_model
):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    normalized = response.json()["results"][0]["normalized"]
    assert normalized is not None
    assert normalized["denominator"]["basis"] == "input_plus_output"
    assert normalized["denominator"]["value"] == pytest.approx(1.0)
    assert normalized["energy"]["min"] == pytest.approx(0.01)
    assert normalized["energy"]["max"] == pytest.approx(0.02)


@pytest.mark.asyncio
async def test_compare_below_minimum_candidates_is_rejected(client, auth_headers):
    payload = {**BASE_REQUEST, "candidates": [{"provider": "openai", "model": "test-only-model"}]}

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_compare_exceeding_candidate_limit_is_rejected(client, auth_headers):
    candidates = [{"provider": "openai", "model": "test-only-model"} for _ in range(11)]
    payload = {**BASE_REQUEST, "candidates": candidates}

    response = await client.post("/v1/compare", json=payload, headers=auth_headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_compare_requires_auth(client):
    payload = {
        **BASE_REQUEST,
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/compare", json=payload)

    assert response.status_code == 401
