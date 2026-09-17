from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.slugs import slugify, with_unique_suffix
from app.models.organization import Organization
from app.models.project import Project
from app.schemas.api_key import ApiKeyCreated
from app.services.api_key_service import ApiKeyService

DEFAULT_PROJECT_NAME = "Default Project"


class OrganizationService:
    """Backs POST /v1/organizations - the one unauthenticated endpoint in
    the API, since it is the account signup step and no auth context can
    exist before it. It bootstraps a default project and first API key
    in the same transaction so the caller has everything needed to make
    their first authenticated request (README "Architecture notes").
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_with_bootstrap(
        self, name: str
    ) -> tuple[Organization, Project, ApiKeyCreated]:
        slug = await self._unique_organization_slug(name)
        organization = Organization(name=name, slug=slug)
        self._db.add(organization)
        await self._db.flush()

        project = Project(
            organization_id=organization.id,
            name=DEFAULT_PROJECT_NAME,
            slug=slugify(DEFAULT_PROJECT_NAME),
        )
        self._db.add(project)
        await self._db.flush()

        api_key, raw_key = ApiKeyService(self._db).stage_new_key(
            organization_id=organization.id,
            project_id=project.id,
            name="Default Key",
            expires_at=None,
        )

        await self._db.commit()
        await self._db.refresh(organization)
        await self._db.refresh(project)
        await self._db.refresh(api_key)

        created_key = ApiKeyCreated(
            id=api_key.id, key=raw_key, key_prefix=api_key.key_prefix, name=api_key.name
        )
        return organization, project, created_key

    async def get_for_organization(self, organization_id: str) -> Organization:
        """Fetches an organization by id. Route callers only ever pass the
        caller's own authenticated organization_id here, so cross-tenant
        access is prevented by construction rather than by an extra check.
        """
        organization = await self._db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError("Organization not found.")
        return organization

    async def _unique_organization_slug(self, name: str) -> str:
        base = slugify(name, fallback="org")
        candidate = base
        for _ in range(5):
            existing = (
                await self._db.execute(select(Organization).where(Organization.slug == candidate))
            ).scalar_one_or_none()
            if existing is None:
                return candidate
            candidate = with_unique_suffix(base)
        return with_unique_suffix(base)
