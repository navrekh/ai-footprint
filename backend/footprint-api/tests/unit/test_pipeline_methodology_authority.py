import pytest

from app.methodology.pipeline import EstimationPipeline
from app.models.enums import MetricStatus
from app.schemas.workload import WorkloadInput
from tests import factories


def _text_generation_workload() -> WorkloadInput:
    return WorkloadInput(
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=100,
        output_tokens=50,
    )


@pytest.mark.asyncio
async def test_dangling_methodology_reference_yields_insufficient_data(db_session):
    """Sprint review item 1: a model may reference a methodology_version
    that has no corresponding Methodology record. Even when factors exist
    under that same (dangling) version string, they must never be used,
    and the response must never claim that version as authoritative.
    """
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(
        db_session, provider_id=provider.id, methodology_version="TEST_ONLY-dangling"
    )
    # Factors exist under the dangling version - proving the fix is not
    # merely "no factors happen to exist" but "the methodology record
    # itself is the gate."
    await factories.create_factor(
        db_session, metric="energy", methodology_version="TEST_ONLY-dangling"
    )
    await factories.create_factor(
        db_session, metric="water", methodology_version="TEST_ONLY-dangling"
    )
    await factories.create_factor(
        db_session, metric="carbon", methodology_version="TEST_ONLY-dangling"
    )
    # Deliberately do NOT create a Methodology row for "TEST_ONLY-dangling".

    result = await EstimationPipeline(db_session).run(_text_generation_workload())

    assert result.energy.status == MetricStatus.INSUFFICIENT_DATA
    assert result.water.status == MetricStatus.INSUFFICIENT_DATA
    assert result.carbon.status == MetricStatus.INSUFFICIENT_DATA
    assert result.energy.min is None
    assert result.methodology_version is None
    assert result.confidence is None
    assert result.evidence_level is None


@pytest.mark.asyncio
async def test_valid_methodology_reference_allows_factor_resolution(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_methodology(db_session, version="TEST_ONLY-0.1")
    await factories.create_model(
        db_session, provider_id=provider.id, methodology_version="TEST_ONLY-0.1"
    )
    await factories.create_factor(
        db_session, metric="energy", methodology_version="TEST_ONLY-0.1"
    )

    result = await EstimationPipeline(db_session).run(_text_generation_workload())

    assert result.energy.status == MetricStatus.OK
    assert result.methodology_version == "TEST_ONLY-0.1"


@pytest.mark.asyncio
async def test_model_with_no_methodology_version_yields_insufficient_data(db_session):
    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    await factories.create_model(db_session, provider_id=provider.id, methodology_version=None)

    result = await EstimationPipeline(db_session).run(_text_generation_workload())

    assert result.energy.status == MetricStatus.INSUFFICIENT_DATA
    assert result.methodology_version is None
