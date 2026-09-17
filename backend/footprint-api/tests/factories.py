import uuid
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key
from app.core.slugs import slugify
from app.models.api_key import ApiKey
from app.models.methodology import Methodology
from app.models.methodology_factor import MethodologyFactor
from app.models.model import Model
from app.models.organization import Organization
from app.models.project import Project
from app.models.provider import Provider

TEST_METHODOLOGY_VERSION = "TEST_ONLY-0.1"


def _unique_slug(name: str) -> str:
    return f"{slugify(name)}-{uuid.uuid4().hex[:8]}"


async def create_organization(session: AsyncSession, name: str = "Test Org") -> Organization:
    org = Organization(name=name, slug=_unique_slug(name))
    session.add(org)
    await session.flush()
    return org


async def create_project(
    session: AsyncSession, organization_id: str, name: str = "Test Project"
) -> Project:
    project = Project(organization_id=organization_id, name=name, slug=_unique_slug(name))
    session.add(project)
    await session.flush()
    return project


async def create_api_key(
    session: AsyncSession,
    project_id: str | None = None,
    *,
    organization_id: str | None = None,
    name: str = "Test Key",
    prefix: str = "afp_test",
    expires_at: datetime | None = None,
) -> tuple[ApiKey, str]:
    """Creates an API key.

    Pass project_id for a project-scoped key (organization_id is derived
    automatically from the project) - the common case, and the same
    call shape Sprint 1's tests already use. Pass organization_id
    directly (with project_id left as None) for an organization-level key.
    """
    if organization_id is None:
        if project_id is None:
            raise ValueError("create_api_key requires organization_id when project_id is None")
        project = await session.get(Project, project_id)
        assert project is not None, f"no project with id {project_id}"
        organization_id = project.organization_id

    raw_key, key_hash, key_prefix = generate_api_key(prefix)
    api_key = ApiKey(
        organization_id=organization_id,
        project_id=project_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        expires_at=expires_at,
    )
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
    version: str | None = None,
    modalities: list[str] | None = None,
    methodology_version: str | None = TEST_METHODOLOGY_VERSION,
    status: str = "active",
    effective_from: date = date(2020, 1, 1),
    effective_to: date | None = None,
) -> Model:
    model = Model(
        provider_id=provider_id,
        name=name,
        version=version,
        modalities=modalities or ["text"],
        methodology_version=methodology_version,
        status=status,
        effective_from=effective_from,
        effective_to=effective_to,
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
