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

    The model registry is versioned, so resolution must be deterministic
    (sprint review, item 2) rather than picking an arbitrary database row:

    - If the caller supplies an explicit ``model_version``, resolve
      provider + name + version exactly (provider_id/name/version is a
      unique constraint, so at most one row can match).
    - Otherwise, resolve the current active version by narrowing
      candidates in order:
        1. effective date - prefer models currently within their
           effective_from/effective_to window;
        2. active status - prefer status == "active" over any other
           status;
        3. deterministic ordering - a fully reproducible sort
           (effective_from, version, id), never database row order.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(
        self,
        provider: Provider,
        model_name: str,
        modality: str,
        model_version: str | None = None,
    ) -> Model:
        result = await self._db.execute(
            select(Model).where(Model.provider_id == provider.id, Model.name == model_name)
        )
        candidates = list(result.scalars().all())
        if not candidates:
            raise ModelNotFoundError(provider.id, model_name)

        if model_version is not None:
            model = self._resolve_explicit_version(
                provider, model_name, candidates, model_version
            )
        else:
            model = self._resolve_current_active(candidates)

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

    @staticmethod
    def _resolve_explicit_version(
        provider: Provider, model_name: str, candidates: list[Model], model_version: str
    ) -> Model:
        matches = [m for m in candidates if m.version == model_version]
        if not matches:
            raise ModelNotFoundError(provider.id, f"{model_name}@{model_version}")
        return matches[0]

    @staticmethod
    def _resolve_current_active(candidates: list[Model]) -> Model:
        today = date.today()

        def in_effective_window(m: Model) -> bool:
            return (m.effective_from is None or m.effective_from <= today) and (
                m.effective_to is None or m.effective_to >= today
            )

        # 1. effective date
        pool = [m for m in candidates if in_effective_window(m)] or candidates

        # 2. active status
        active_only = [m for m in pool if m.status == ModelStatus.ACTIVE.value]
        pool = active_only or pool

        # 3. deterministic ordering - never depend on database row order
        pool = sorted(pool, key=lambda m: (m.effective_from or date.min, m.version or "", m.id))
        return pool[-1]
