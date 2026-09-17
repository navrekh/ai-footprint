from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ModelNotFoundError, ModelNotSupportedError
from app.models.enums import ModelStatus
from app.models.model import Model
from app.models.provider import Provider


class ModelResolver:
    """Pipeline stage 3: resolves the canonical Model registry entry
    belonging to the already-resolved provider.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(self, provider: Provider, model_name: str, modality: str) -> Model:
        result = await self._db.execute(
            select(Model).where(Model.provider_id == provider.id, Model.name == model_name)
        )
        candidates = list(result.scalars().all())
        if not candidates:
            raise ModelNotFoundError(provider.id, model_name)

        today = date.today()
        active = [
            m
            for m in candidates
            if (m.effective_from is None or m.effective_from <= today)
            and (m.effective_to is None or m.effective_to >= today)
        ]
        model = (active or candidates)[0]

        if model.status == ModelStatus.DEPRECATED.value:
            raise ModelNotSupportedError(
                f"Model '{model_name}' from provider '{provider.id}' is deprecated and no "
                "longer supported."
            )
        if modality not in model.modalities:
            raise ModelNotSupportedError(
                f"Model '{model_name}' does not support modality '{modality}'."
            )
        return model
