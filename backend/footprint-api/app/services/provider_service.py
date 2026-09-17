from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import Provider


class ProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_providers(self) -> list[Provider]:
        result = await self._db.execute(select(Provider).order_by(Provider.id))
        return list(result.scalars().all())
