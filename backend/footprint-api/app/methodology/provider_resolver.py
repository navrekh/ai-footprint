from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProviderNotFoundError
from app.models.provider import Provider


class ProviderResolver:
    """Pipeline stage 2: resolves the canonical Provider registry entry."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(self, provider_id: str) -> Provider:
        normalized = provider_id.strip().lower()
        result = await self._db.execute(select(Provider).where(Provider.id == normalized))
        provider = result.scalar_one_or_none()
        if provider is None:
            raise ProviderNotFoundError(provider_id)
        return provider
