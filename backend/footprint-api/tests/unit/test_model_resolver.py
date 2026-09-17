import pytest

from app.core.errors import ModelNotFoundError, ModelNotSupportedError
from app.methodology.model_resolver import ModelResolver
from tests import factories


@pytest.mark.asyncio
async def test_resolves_active_model(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, modalities=["text"])
    resolver = ModelResolver(db_session)

    model = await resolver.resolve(provider, "test-only-model", "text")

    assert model.name == "test-only-model"


@pytest.mark.asyncio
async def test_unknown_model_raises(db_session):
    provider = await factories.create_provider(db_session, "openai")
    resolver = ModelResolver(db_session)

    with pytest.raises(ModelNotFoundError):
        await resolver.resolve(provider, "does-not-exist", "text")


@pytest.mark.asyncio
async def test_deprecated_model_not_supported(db_session):
    provider = await factories.create_provider(db_session, "openai")
    await factories.create_model(db_session, provider_id=provider.id, status="deprecated")
    resolver = ModelResolver(db_session)

    with pytest.raises(ModelNotSupportedError):
        await resolver.resolve(provider, "test-only-model", "text")


@pytest.mark.asyncio
async def test_unsupported_modality_not_supported(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, modalities=["text"])
    resolver = ModelResolver(db_session)

    with pytest.raises(ModelNotSupportedError):
        await resolver.resolve(provider, "test-only-model", "image")
