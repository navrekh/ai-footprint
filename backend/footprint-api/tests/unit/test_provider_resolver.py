import pytest

from app.core.errors import ProviderNotFoundError
from app.methodology.provider_resolver import ProviderResolver
from tests import factories


@pytest.mark.asyncio
async def test_resolves_existing_provider(db_session):
    await factories.create_provider(db_session, "openai")
    resolver = ProviderResolver(db_session)

    provider = await resolver.resolve("openai")

    assert provider.id == "openai"


@pytest.mark.asyncio
async def test_resolve_is_case_insensitive(db_session):
    await factories.create_provider(db_session, "openai")
    resolver = ProviderResolver(db_session)

    provider = await resolver.resolve("OpenAI")

    assert provider.id == "openai"


@pytest.mark.asyncio
async def test_unknown_provider_raises(db_session):
    resolver = ProviderResolver(db_session)

    with pytest.raises(ProviderNotFoundError):
        await resolver.resolve("does-not-exist")
