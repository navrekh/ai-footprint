import pytest


@pytest.mark.asyncio
async def test_list_benchmarks_is_deterministic_and_public(client):
    first = await client.get("/v1/benchmarks")
    second = await client.get("/v1/benchmarks")

    assert first.status_code == 200
    assert second.status_code == 200
    assert [b["benchmark_id"] for b in first.json()["items"]] == [
        b["benchmark_id"] for b in second.json()["items"]
    ]
    assert first.json()["total"] == len(first.json()["items"])


@pytest.mark.asyncio
async def test_list_benchmarks_every_item_has_a_version(client):
    response = await client.get("/v1/benchmarks")

    for item in response.json()["items"]:
        assert item["version"]


@pytest.mark.asyncio
async def test_list_benchmarks_filter_by_activity_type(client):
    response = await client.get("/v1/benchmarks", params={"activity_type": "code_review"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert all(item["activity_type"] == "code_review" for item in items)


@pytest.mark.asyncio
async def test_list_benchmarks_filter_by_modality(client):
    response = await client.get("/v1/benchmarks", params={"modality": "audio"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert all(item["modality"] == "audio" for item in items)


@pytest.mark.asyncio
async def test_get_benchmark_by_id(client):
    response = await client.get("/v1/benchmarks/text_generation_standard")

    assert response.status_code == 200
    body = response.json()
    assert body["benchmark_id"] == "text_generation_standard"
    assert body["parameters"]["input_tokens"] == 500


@pytest.mark.asyncio
async def test_get_unknown_benchmark_returns_404(client):
    response = await client.get("/v1/benchmarks/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "BENCHMARK_NOT_FOUND"


@pytest.mark.asyncio
async def test_benchmark_get_endpoints_work_without_authorization_header(client):
    list_response = await client.get("/v1/benchmarks")
    get_response = await client.get("/v1/benchmarks/text_generation_standard")

    assert list_response.status_code == 200
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_run_benchmark_against_test_only_fixture_succeeds(
    client, auth_headers, wired_model
):
    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["benchmark_id"] == "text_generation_standard"
    assert body["benchmark_version"] == "1.0"
    assert len(body["results"]) == 2
    for item in body["results"]:
        assert item["status"] == "success"
        assert item["estimate"]["energy"]["status"] == "ok"


@pytest.mark.asyncio
async def test_run_benchmark_reports_insufficient_data_without_fabrication(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session)
    await factories.create_model(db_session, provider_id=provider.id, name="no-factor-model")
    # No factors seeded - insufficient_data is the only correct outcome,
    # never a fabricated coefficient.
    await db_session.commit()

    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "no-factor-model"},
            {"provider": "openai", "model": "no-factor-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)

    body = response.json()
    for result in body["results"]:
        assert result["status"] == "success"
        assert result["estimate"]["energy"]["status"] == "insufficient_data"
        assert result["estimate"]["energy"]["min"] is None
        assert result["estimate"]["energy"]["max"] is None


@pytest.mark.asyncio
async def test_run_benchmark_unknown_model_failure_isolated_per_candidate(
    client, auth_headers, db_session
):
    from tests import factories

    await factories.create_provider(db_session, "openai", modalities=["text"])
    await db_session.commit()

    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "no-such-model"},
            {"provider": "openai", "model": "no-such-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)

    body = response.json()
    for item in body["results"]:
        assert item["status"] == "failed"
        assert item["error"]["code"] == "MODEL_NOT_FOUND"


@pytest.mark.asyncio
async def test_run_unknown_benchmark_returns_404(client, auth_headers):
    payload = {
        "benchmark_id": "does-not-exist",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "BENCHMARK_NOT_FOUND"


@pytest.mark.asyncio
async def test_run_benchmark_requires_auth(client):
    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    response = await client.post("/v1/benchmarks/run", json=payload)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_benchmark_is_reproducible_with_unchanged_data(
    client, auth_headers, wired_model
):
    payload = {
        "benchmark_id": "text_generation_standard",
        "candidates": [
            {"provider": "openai", "model": "test-only-model"},
            {"provider": "openai", "model": "test-only-model"},
        ],
    }

    first = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)
    second = await client.post("/v1/benchmarks/run", json=payload, headers=auth_headers)

    first_estimates = [r["estimate"] for r in first.json()["results"]]
    second_estimates = [r["estimate"] for r in second.json()["results"]]
    for f, s in zip(first_estimates, second_estimates, strict=True):
        assert f["energy"] == s["energy"]
        assert f["water"] == s["water"]
        assert f["carbon"] == s["carbon"]
        assert f["methodology_version"] == s["methodology_version"]
