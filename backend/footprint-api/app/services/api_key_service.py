from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.core.security import generate_api_key
from app.db.base import utcnow
from app.models.api_key import ApiKey
from app.models.enums import ApiKeyStatus
from app.schemas.api_key import ApiKeyCreated


class ApiKeyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def stage_new_key(
        self,
        *,
        organization_id: str,
        project_id: str | None,
        name: str,
        expires_at: datetime | None,
    ) -> tuple[ApiKey, str]:
        """Constructs and stages (add, no flush/commit) a new ApiKey row.

        Public but intentionally not "the" way to create a key from a
        route - use create() for that. This exists so OrganizationService
        can bootstrap an organization, its default project and its first
        key in a single transaction without this service committing out
        from under it.
        """
        settings = get_settings()
        raw_key, key_hash, key_prefix = generate_api_key(settings.API_KEY_PREFIX)
        api_key = ApiKey(
            organization_id=organization_id,
            project_id=project_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            status=ApiKeyStatus.ACTIVE.value,
            expires_at=expires_at,
        )
        self._db.add(api_key)
        return api_key, raw_key

    async def create(
        self,
        *,
        organization_id: str,
        project_id: str | None,
        name: str,
        expires_at: datetime | None = None,
    ) -> ApiKeyCreated:
        api_key, raw_key = self.stage_new_key(
            organization_id=organization_id,
            project_id=project_id,
            name=name,
            expires_at=expires_at,
        )
        await self._db.commit()
        await self._db.refresh(api_key)
        return ApiKeyCreated(
            id=api_key.id, key=raw_key, key_prefix=api_key.key_prefix, name=api_key.name
        )

    async def list_for_organization(
        self, organization_id: str, *, limit: int, offset: int
    ) -> tuple[list[ApiKey], int]:
        total = (
            await self._db.execute(
                select(func.count())
                .select_from(ApiKey)
                .where(ApiKey.organization_id == organization_id)
            )
        ).scalar_one()
        result = await self._db.execute(
            select(ApiKey)
            .where(ApiKey.organization_id == organization_id)
            .order_by(ApiKey.created_at.desc(), ApiKey.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def revoke(self, organization_id: str, api_key_id: str) -> ApiKey:
        api_key = await self._get_owned(organization_id, api_key_id)
        api_key.status = ApiKeyStatus.REVOKED.value
        api_key.revoked_at = utcnow()
        await self._db.commit()
        await self._db.refresh(api_key)
        return api_key

    async def _get_owned(self, organization_id: str, api_key_id: str) -> ApiKey:
        result = await self._db.execute(
            select(ApiKey).where(
                ApiKey.id == api_key_id, ApiKey.organization_id == organization_id
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            # Never distinguish "belongs to another org" from "does not
            # exist" - both return 404 (sprint review, tenant isolation).
            raise NotFoundError("API key not found.")
        return api_key
