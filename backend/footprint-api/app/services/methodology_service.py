from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.methodology import Methodology


class MethodologyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_methodologies(self) -> list[Methodology]:
        result = await self._db.execute(select(Methodology).order_by(Methodology.effective_date))
        return list(result.scalars().all())
