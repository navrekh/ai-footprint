import pytest

from app.methodology.factor_repository import FactorRepository
from tests import factories


@pytest.mark.asyncio
async def test_returns_none_when_no_factor_exists(db_session):
    repo = FactorRepository(db_session)

    factor = await repo.find_best_factor(
        metric="energy",
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        methodology_version="TEST_ONLY-0.1",
    )

    assert factor is None


@pytest.mark.asyncio
async def test_prefers_provider_and_model_specific_factor_over_generic(db_session):
    repo = FactorRepository(db_session)

    generic = await factories.create_factor(
        db_session, metric="energy", provider=None, model=None, value_min=0.5, value_max=0.5
    )
    specific = await factories.create_factor(
        db_session,
        metric="energy",
        provider="openai",
        model="test-only-model",
        value_min=0.01,
        value_max=0.02,
    )

    factor = await repo.find_best_factor(
        metric="energy",
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        methodology_version="TEST_ONLY-0.1",
    )

    assert factor is not None
    assert factor.factor_id == specific.factor_id
    assert factor.factor_id != generic.factor_id


@pytest.mark.asyncio
async def test_falls_back_to_generic_factor_when_no_specific_factor_exists(db_session):
    repo = FactorRepository(db_session)

    generic = await factories.create_factor(
        db_session, metric="energy", provider=None, model=None, value_min=0.5, value_max=0.5
    )

    factor = await repo.find_best_factor(
        metric="energy",
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        methodology_version="TEST_ONLY-0.1",
    )

    assert factor is not None
    assert factor.factor_id == generic.factor_id


@pytest.mark.asyncio
async def test_does_not_match_different_methodology_version(db_session):
    repo = FactorRepository(db_session)
    await factories.create_factor(
        db_session, metric="energy", methodology_version="TEST_ONLY-0.2"
    )

    factor = await repo.find_best_factor(
        metric="energy",
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        methodology_version="TEST_ONLY-0.1",
    )

    assert factor is None
