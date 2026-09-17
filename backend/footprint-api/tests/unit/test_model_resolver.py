from datetime import date

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


@pytest.mark.asyncio
async def test_single_version_resolves_without_explicit_version(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, version="v1")
    resolver = ModelResolver(db_session)

    model = await resolver.resolve(provider, "test-only-model", "text")

    assert model.version == "v1"


@pytest.mark.asyncio
async def test_multiple_versions_without_explicit_version_picks_current_active(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v1",
        effective_from=date(2020, 1, 1),
        effective_to=date(2020, 12, 31),
    )
    current = await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v2",
        effective_from=date(2021, 1, 1),
        effective_to=None,
    )
    resolver = ModelResolver(db_session)

    model = await resolver.resolve(provider, "test-only-model", "text")

    assert model.id == current.id
    assert model.version == "v2"


@pytest.mark.asyncio
async def test_explicit_version_resolves_exact_match(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    old = await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v1",
        effective_from=date(2020, 1, 1),
        effective_to=date(2020, 12, 31),
    )
    await factories.create_model(
        db_session, provider_id=provider.id, version="v2", effective_from=date(2021, 1, 1)
    )
    resolver = ModelResolver(db_session)

    model = await resolver.resolve(provider, "test-only-model", "text", model_version="v1")

    assert model.id == old.id


@pytest.mark.asyncio
async def test_explicit_unknown_version_raises_model_not_found(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, version="v1")
    resolver = ModelResolver(db_session)

    with pytest.raises(ModelNotFoundError):
        await resolver.resolve(provider, "test-only-model", "text", model_version="v99")


@pytest.mark.asyncio
async def test_explicit_deprecated_version_is_rejected(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(
        db_session, provider_id=provider.id, version="v1", status="deprecated"
    )
    resolver = ModelResolver(db_session)

    with pytest.raises(ModelNotSupportedError):
        await resolver.resolve(provider, "test-only-model", "text", model_version="v1")


@pytest.mark.asyncio
async def test_auto_resolution_prefers_active_over_deprecated(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v1",
        status="deprecated",
        effective_from=date(2020, 1, 1),
    )
    active = await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v2",
        status="active",
        effective_from=date(2019, 1, 1),
    )
    resolver = ModelResolver(db_session)

    model = await resolver.resolve(provider, "test-only-model", "text")

    # Active status wins even though v1 has a more recent effective_from -
    # step 2 (active status) narrows before step 3 (deterministic tiebreak).
    assert model.id == active.id


@pytest.mark.asyncio
async def test_auto_resolution_ignores_not_yet_effective_version(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    current = await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v1",
        effective_from=date(2020, 1, 1),
        effective_to=None,
    )
    await factories.create_model(
        db_session,
        provider_id=provider.id,
        version="v2-future",
        effective_from=date(2999, 1, 1),
        effective_to=None,
    )
    resolver = ModelResolver(db_session)

    model = await resolver.resolve(provider, "test-only-model", "text")

    assert model.id == current.id


@pytest.mark.asyncio
async def test_auto_resolution_is_deterministic_across_repeated_calls(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(
        db_session, provider_id=provider.id, version="v1", effective_from=date(2020, 1, 1)
    )
    await factories.create_model(
        db_session, provider_id=provider.id, version="v2", effective_from=date(2020, 1, 1)
    )
    resolver = ModelResolver(db_session)

    first = await resolver.resolve(provider, "test-only-model", "text")
    second = await resolver.resolve(provider, "test-only-model", "text")

    assert first.id == second.id
