import pytest


@pytest.mark.asyncio
async def test_list_providers_is_public(client, db_session):
    from tests import factories

    await factories.create_provider(db_session, "openai", modalities=["text", "image"])
    await db_session.commit()

    response = await client.get("/v1/providers")

    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert "openai" in ids


@pytest.mark.asyncio
async def test_list_models_filters_by_provider_and_modality(client, db_session):
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text", "image"])
    await factories.create_model(
        db_session, provider_id=provider.id, name="text-model", modalities=["text"]
    )
    await factories.create_model(
        db_session, provider_id=provider.id, name="image-model", modalities=["image"]
    )
    await db_session.commit()

    response = await client.get("/v1/models", params={"provider": "openai", "modality": "image"})

    assert response.status_code == 200
    names = [m["name"] for m in response.json()]
    assert names == ["image-model"]


@pytest.mark.asyncio
async def test_list_methodology_versions(client, db_session):
    from tests import factories

    await factories.create_methodology(db_session, version="TEST_ONLY-0.1")
    await db_session.commit()

    response = await client.get("/v1/methodology")

    assert response.status_code == 200
    versions = [m["version"] for m in response.json()]
    assert "TEST_ONLY-0.1" in versions
