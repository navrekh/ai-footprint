"""Seeds baseline reference data for local development.

By default this seeds only real, non-fabricated registry metadata
(providers) plus a demo organization/project/API key so a developer can
immediately call protected endpoints. It never seeds environmental
coefficients on its own - per data/methodology/README.md, that requires a
reviewed, sourced methodology factor, which does not exist yet.

Pass --with-test-only-demo-data to additionally seed a methodology
version, model and factor set that is unambiguously marked TEST_ONLY, so
that /v1/estimate and /v1/events can be exercised end-to-end locally.
These values must never be treated as real measurements and must never be
seeded into a shared/staging/production database.
"""

import argparse
import asyncio
from datetime import date

from sqlalchemy import select

from app.core.slugs import slugify
from app.db.database import AsyncSessionLocal
from app.models.api_key import ApiKey
from app.models.methodology import Methodology
from app.models.methodology_factor import MethodologyFactor
from app.models.model import Model
from app.models.organization import Organization
from app.models.project import Project
from app.models.provider import Provider
from app.services.api_key_service import ApiKeyService

PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "supported_modalities": ["text", "image", "audio", "coding"],
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "supported_modalities": ["text", "coding"],
    },
    {
        "id": "google",
        "name": "Google",
        "supported_modalities": ["text", "image", "video", "audio", "coding"],
    },
]

DEMO_ORG_NAME = "Demo Organization"
DEMO_PROJECT_NAME = "Demo Project"
DEMO_KEY_NAME = "Seed Default Key"

TEST_ONLY_METHODOLOGY_VERSION = "TEST_ONLY-0.1"
TEST_ONLY_PROVIDER = "openai"
TEST_ONLY_MODEL_NAME = "test-only-demo-model"


async def seed_providers(session) -> None:
    for entry in PROVIDERS:
        existing = await session.get(Provider, entry["id"])
        if existing is not None:
            continue
        session.add(
            Provider(
                id=entry["id"],
                name=entry["name"],
                supported_modalities=entry["supported_modalities"],
            )
        )
    await session.commit()
    print(f"Seeded providers: {', '.join(p['id'] for p in PROVIDERS)}")


async def seed_demo_org_project_and_key(session) -> None:
    org = (
        await session.execute(select(Organization).where(Organization.name == DEMO_ORG_NAME))
    ).scalar_one_or_none()
    if org is None:
        org = Organization(name=DEMO_ORG_NAME, slug=slugify(DEMO_ORG_NAME, fallback="org"))
        session.add(org)
        await session.commit()
        await session.refresh(org)
        print(f"Created organization: {org.id}")
    else:
        print(f"Organization already exists: {org.id}")

    project = (
        await session.execute(
            select(Project).where(
                Project.organization_id == org.id, Project.name == DEMO_PROJECT_NAME
            )
        )
    ).scalar_one_or_none()
    if project is None:
        project = Project(
            organization_id=org.id,
            name=DEMO_PROJECT_NAME,
            slug=slugify(DEMO_PROJECT_NAME, fallback="project"),
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        print(f"Created project: {project.id}")
    else:
        print(f"Project already exists: {project.id}")

    existing_key = (
        await session.execute(
            select(ApiKey).where(ApiKey.project_id == project.id, ApiKey.name == DEMO_KEY_NAME)
        )
    ).scalar_one_or_none()
    if existing_key is not None:
        print(
            f"API key '{DEMO_KEY_NAME}' already exists for project {project.id} "
            "(the raw key is only ever shown once, at creation time)."
        )
        return

    created = await ApiKeyService(session).create(
        organization_id=org.id, project_id=project.id, name=DEMO_KEY_NAME
    )
    print("Created API key - save this now, it will not be shown again:")
    print(f"  {created.key}")


async def seed_test_only_demo_data(session) -> None:
    print(
        "\n[WARNING] Seeding TEST_ONLY synthetic demo data. These are NOT real "
        "environmental measurements - they exist only to exercise the "
        "estimation engine end-to-end in local development. Never run this "
        "against a shared, staging or production database."
    )

    existing_methodology = (
        await session.execute(
            select(Methodology).where(Methodology.version == TEST_ONLY_METHODOLOGY_VERSION)
        )
    ).scalar_one_or_none()
    if existing_methodology is None:
        session.add(
            Methodology(
                version=TEST_ONLY_METHODOLOGY_VERSION,
                description=(
                    "TEST_ONLY synthetic methodology used solely to exercise the estimation "
                    "engine in local development. Not an approved production methodology."
                ),
                effective_date=date(2020, 1, 1),
                sources=["TEST_ONLY - no real source; synthetic fixture."],
                assumptions=["TEST_ONLY fixture value - not derived from any measurement."],
                limitations=["Must never be used for real reporting."],
            )
        )
        await session.commit()

    existing_model = (
        await session.execute(
            select(Model).where(
                Model.provider_id == TEST_ONLY_PROVIDER, Model.name == TEST_ONLY_MODEL_NAME
            )
        )
    ).scalar_one_or_none()
    if existing_model is None:
        session.add(
            Model(
                provider_id=TEST_ONLY_PROVIDER,
                name=TEST_ONLY_MODEL_NAME,
                modalities=["text"],
                methodology_version=TEST_ONLY_METHODOLOGY_VERSION,
                effective_from=date(2020, 1, 1),
            )
        )
        await session.commit()

    factor_specs = [
        ("energy", "Wh", 0.01, 0.02),
        ("water", "mL", 0.01, 0.02),
        ("carbon", "gCO2e", 0.001, 0.002),
    ]
    for metric, unit, value_min, value_max in factor_specs:
        factor_id = (
            f"TEST_ONLY-{TEST_ONLY_PROVIDER}-{TEST_ONLY_MODEL_NAME}-text_generation-{metric}"
        )
        existing_factor = (
            await session.execute(
                select(MethodologyFactor).where(MethodologyFactor.factor_id == factor_id)
            )
        ).scalar_one_or_none()
        if existing_factor is not None:
            continue
        session.add(
            MethodologyFactor(
                factor_id=factor_id,
                metric=metric,
                provider=TEST_ONLY_PROVIDER,
                model=TEST_ONLY_MODEL_NAME,
                modality="text",
                activity_type="text_generation",
                value_min=value_min,
                value_max=value_max,
                unit=unit,
                evidence_level=6,
                confidence="low",
                source=(
                    "TEST_ONLY - synthetic fixture value for engine validation, "
                    "not a real measurement."
                ),
                source_date=date(2020, 1, 1),
                accounting_boundary="A",
                effective_from=date(2020, 1, 1),
                methodology_version=TEST_ONLY_METHODOLOGY_VERSION,
                assumptions=["TEST_ONLY fixture - not a real measurement."],
                limitations=["Must never be used for real reporting."],
            )
        )
    await session.commit()
    print(
        f"Seeded TEST_ONLY model '{TEST_ONLY_MODEL_NAME}' and factors under provider "
        f"'{TEST_ONLY_PROVIDER}' with methodology_version={TEST_ONLY_METHODOLOGY_VERSION}."
    )


async def main(with_test_only_demo_data: bool) -> None:
    async with AsyncSessionLocal() as session:
        await seed_providers(session)
        await seed_demo_org_project_and_key(session)
        if with_test_only_demo_data:
            await seed_test_only_demo_data(session)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed baseline AI Footprint reference data.")
    parser.add_argument(
        "--with-test-only-demo-data",
        action="store_true",
        help=(
            "Also seed a TEST_ONLY methodology/model/factor set so /v1/estimate can be "
            "exercised locally end-to-end. Never enable this against a shared, staging or "
            "production database."
        ),
    )
    args = parser.parse_args()
    asyncio.run(main(args.with_test_only_demo_data))
