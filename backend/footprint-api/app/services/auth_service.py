from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiKeyExpiredError, InvalidApiKeyError
from app.core.security import hash_api_key
from app.db.base import utcnow
from app.models.api_key import ApiKey
from app.models.enums import ApiKeyStatus
from app.models.organization import Organization
from app.models.project import Project


class AuthContext:
    """The resolved API key -> organization (-> optional project) chain
    for a request.

    project is None for an organization-level key (used to bootstrap and
    manage projects/keys before any project-scoped key exists for a given
    project) and set for a project-scoped key, which behaves exactly as
    in Sprint 1.
    """

    def __init__(
        self, api_key: ApiKey, organization: Organization, project: Project | None
    ) -> None:
        self.api_key = api_key
        self.organization = organization
        self.project = project


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def authenticate(self, raw_key: str) -> AuthContext:
        key_hash = hash_api_key(raw_key)
        api_key = (
            await self._db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        ).scalar_one_or_none()
        if api_key is None or api_key.status != ApiKeyStatus.ACTIVE.value:
            raise InvalidApiKeyError()

        now = utcnow()
        if api_key.expires_at is not None and api_key.expires_at <= now:
            raise ApiKeyExpiredError()

        organization = (
            await self._db.execute(
                select(Organization).where(Organization.id == api_key.organization_id)
            )
        ).scalar_one_or_none()
        if organization is None:
            raise InvalidApiKeyError()

        project: Project | None = None
        if api_key.project_id is not None:
            project = (
                await self._db.execute(select(Project).where(Project.id == api_key.project_id))
            ).scalar_one_or_none()
            if project is None:
                raise InvalidApiKeyError()

        # Direct UPDATE (no ORM load/mutate round trip) to keep the auth
        # path cheap on every authenticated request.
        await self._db.execute(
            update(ApiKey).where(ApiKey.id == api_key.id).values(last_used_at=now)
        )
        await self._db.commit()

        return AuthContext(api_key=api_key, organization=organization, project=project)
