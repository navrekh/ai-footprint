from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key
from app.models.api_key import ApiKey
from app.models.methodology import Methodology
from app.models.methodology_factor import MethodologyFactor
from app.models.model import Model
from app.models.organization import Organization
from app.models.project import Project
from app.models.provider import Provider

TEST_METHODOLOGY_VERSION = "TEST_ONLY-0.1"


async def create_organization(session: AsyncSession, name: str = "Test Org") -> Organization:
    org = Organization(name=name)
    session.add(org)
    await session.flush()
    return org


async def create_project(
    session: AsyncSession, organization_id: str, name: str = "Test Project"
) -> Project:
    project = Project(organization_id=organization_id, name=name)
    session.add(project)
    await session.flush()
    return project


async def create_api_key(
    session: AsyncSession, project_id: str, name: str = "Test Key", prefix: str = "afp_test"
) -> tuple[ApiKey, str]:
    raw_key, key_hash, key_prefix = generate_api_key(prefix)
    api_key = ApiKey(project_id=project_id, key_hash=key_hash, key_prefix=key_prefix, name=name)
    session.add(api_key)
    await session.flush()
    return api_key, raw_key


async def create_provider(
    session: AsyncSession, provider_id: str = "openai", modalities: list[str] | None = None
) -> Provider:
    provider = Provider(
        id=provider_id, name=provider_id.title(), supported_modalities=modalities or ["text"]
    )
    session.add(provider)
    await session.flush()
    return provider


async def create_methodology(
    session: AsyncSession, version: str = TEST_METHODOLOGY_VERSION
) -> Methodology:
    methodology = Methodology(
        version=version,
        description="TEST_ONLY fixture methodology used only in the automated test suite.",
        effective_date=date(2020, 1, 1),
        sources=["TEST_ONLY - no real source; synthetic fixture."],
        assumptions=["TEST_ONLY fixture value - not derived from any measurement."],
        limitations=["Must never be used for real reporting."],
    )
    session.add(methodology)
    await session.flush()
    return methodology


async def create_model(
    session: AsyncSession,
    provider_id: str = "openai",
    name: str = "test-only-model",
    modalities: list[str] | None = None,
    methodology_version: str | None = TEST_METHODOLOGY_VERSION,
    status: str = "active",
) -> Model:
    model = Model(
        provider_id=provider_id,
        name=name,
        modalities=modalities or ["text"],
        methodology_version=methodology_version,
        status=status,
        effective_from=date(2020, 1, 1),
    )
    session.add(model)
    await session.flush()
    return model


async def create_factor(
    session: AsyncSession,
    *,
    metric: str,
    provider: str | None = "openai",
    model: str | None = "test-only-model",
    modality: str = "text",
    activity_type: str = "text_generation",
    value_min: float = 0.01,
    value_max: float = 0.02,
    unit: str = "Wh",
    methodology_version: str = TEST_METHODOLOGY_VERSION,
    evidence_level: int = 6,
    confidence: str = "low",
) -> MethodologyFactor:
    factor_id = (
        f"TEST_ONLY-{provider}-{model}-{modality}-{activity_type}-{metric}-{value_min}-{value_max}"
    )
    factor = MethodologyFactor(
        factor_id=factor_id,
        metric=metric,
        provider=provider,
        model=model,
        modality=modality,
        activity_type=activity_type,
        value_min=value_min,
        value_max=value_max,
        unit=unit,
        evidence_level=evidence_level,
        confidence=confidence,
        source="TEST_ONLY - synthetic fixture value for automated tests, not a real measurement.",
        source_date=date(2020, 1, 1),
        accounting_boundary="A",
        effective_from=date(2020, 1, 1),
        methodology_version=methodology_version,
        assumptions=["TEST_ONLY fixture - not a real measurement."],
        limitations=["Must never be used for real reporting."],
    )
    session.add(factor)
    await session.flush()
    return factor
