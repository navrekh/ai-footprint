import pytest

from app.methodology.methodology_resolver import MethodologyResolver
from tests import factories


@pytest.mark.asyncio
async def test_resolves_existing_methodology_version(db_session):
    await factories.create_methodology(db_session, version="TEST_ONLY-0.1")
    resolver = MethodologyResolver(db_session)

    methodology = await resolver.resolve("TEST_ONLY-0.1")

    assert methodology is not None
    assert methodology.version == "TEST_ONLY-0.1"


@pytest.mark.asyncio
async def test_missing_methodology_version_returns_none(db_session):
    resolver = MethodologyResolver(db_session)

    methodology = await resolver.resolve("does-not-exist")

    assert methodology is None


@pytest.mark.asyncio
async def test_none_version_returns_none(db_session):
    resolver = MethodologyResolver(db_session)

    methodology = await resolver.resolve(None)

    assert methodology is None
