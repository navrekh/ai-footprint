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
async def test_get_estimate_by_id(client, auth_headers, wired_model):
    create_response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    estimate_id = create_response.json()["estimate_id"]
    workload_id = create_response.json()["workload_id"]

    response = await client.get(f"/v1/estimates/{estimate_id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["estimate_id"] == estimate_id
    assert body["workload_id"] == workload_id
    assert body["provider"] == "openai"
    assert body["model"] == "test-only-model"
    assert body["status"] == "measured"
    assert body["energy"]["status"] == "ok"


@pytest.mark.asyncio
async def test_get_estimate_preserves_insufficient_data_status(
    client, auth_headers, db_session
):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, methodology_version=None)
    await db_session.commit()

    create_response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    estimate_id = create_response.json()["estimate_id"]

    response = await client.get(f"/v1/estimates/{estimate_id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["energy"]["min"] is None
    assert body["energy"]["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_get_unknown_estimate_returns_not_found(client, auth_headers):
    response = await client.get("/v1/estimates/est_does_not_exist", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_estimate_rejects_cross_tenant_access(
    client, auth_headers, wired_model, db_session
):
    from tests import factories

    create_response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)
    estimate_id = create_response.json()["estimate_id"]

    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    _, other_raw_key = await factories.create_api_key(db_session, other_project.id)
    await db_session.commit()

    response = await client.get(
        f"/v1/estimates/{estimate_id}", headers={"Authorization": f"Bearer {other_raw_key}"}
    )

    assert response.status_code == 404
