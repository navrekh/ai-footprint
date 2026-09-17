from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidApiKeyError
from app.core.security import hash_api_key
from app.db.base import utcnow
from app.models.api_key import ApiKey
from app.models.enums import ApiKeyStatus
from app.models.organization import Organization
from app.models.project import Project


class AuthContext:
    """The resolved API key -> project -> organization chain for a request."""

    def __init__(self, api_key: ApiKey, project: Project, organization: Organization) -> None:
        self.api_key = api_key
        self.project = project
        self.organization = organization


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def authenticate(self, raw_key: str) -> AuthContext:
        key_hash = hash_api_key(raw_key)
        result = await self._db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        api_key = result.scalar_one_or_none()
        if api_key is None or api_key.status != ApiKeyStatus.ACTIVE.value:
            raise InvalidApiKeyError()

        project = (
            await self._db.execute(select(Project).where(Project.id == api_key.project_id))
        ).scalar_one_or_none()
        if project is None:
            raise InvalidApiKeyError()

        organization = (
            await self._db.execute(
                select(Organization).where(Organization.id == project.organization_id)
            )
        ).scalar_one_or_none()
        if organization is None:
            raise InvalidApiKeyError()

        # Direct UPDATE (no ORM load/mutate round trip) to keep the auth
        # path cheap on every authenticated request.
        await self._db.execute(
            update(ApiKey).where(ApiKey.id == api_key.id).values(last_used_at=utcnow())
        )
        await self._db.commit()

        return AuthContext(api_key=api_key, project=project, organization=organization)
