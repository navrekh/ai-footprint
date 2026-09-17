from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model


class ModelService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_models(
        self,
        provider_id: str | None = None,
        modality: str | None = None,
        status: str | None = None,
    ) -> list[Model]:
        stmt = select(Model)
        if provider_id:
            stmt = stmt.where(Model.provider_id == provider_id)
        if status:
            stmt = stmt.where(Model.status == status)
        result = await self._db.execute(stmt.order_by(Model.name))
        models = list(result.scalars().all())
        if modality:
            models = [m for m in models if modality in m.modalities]
        return models
