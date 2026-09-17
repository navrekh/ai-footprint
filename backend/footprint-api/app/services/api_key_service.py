from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_api_key
from app.db.base import utcnow
from app.models.api_key import ApiKey
from app.models.enums import ApiKeyStatus
from app.schemas.api_key import ApiKeyCreated


class ApiKeyService:
    """Provisioning is not yet exposed over HTTP in Sprint 1 (the sprint's
    endpoint list has no account/project/key-management routes - see
    README "Architecture notes"). This service backs the seed script and
    is the natural home for a future POST /v1/api-keys endpoint.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, project_id: str, name: str) -> ApiKeyCreated:
        settings = get_settings()
        raw_key, key_hash, key_prefix = generate_api_key(settings.API_KEY_PREFIX)
        api_key = ApiKey(
            project_id=project_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            status=ApiKeyStatus.ACTIVE.value,
        )
        self._db.add(api_key)
        await self._db.commit()
        await self._db.refresh(api_key)
        return ApiKeyCreated(
            id=api_key.id, raw_key=raw_key, key_prefix=key_prefix, name=api_key.name
        )

    async def revoke(self, api_key: ApiKey) -> None:
        api_key.status = ApiKeyStatus.REVOKED.value
        api_key.revoked_at = utcnow()
        await self._db.commit()
