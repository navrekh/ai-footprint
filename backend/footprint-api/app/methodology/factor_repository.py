from collections.abc import Callable
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.methodology_factor import MethodologyFactor


class FactorRepository:
    """Resolves the most specific applicable methodology factor for a
    metric, following the precedence order defined in
    data/methodology/README.md:

      1. provider + model + activity (+ region + hardware, when the
         factor is explicitly scoped to a region/hardware combination)
      2. provider + model + activity
      3. provider + modality + activity (no specific model)
      4. model-scoped research factor with no specific provider
      5. approved generic workload factor (no provider, no model)
      6. no factor -> insufficient_data (returns None)
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def find_best_factor(
        self,
        *,
        metric: str,
        provider: str,
        model: str,
        modality: str,
        activity_type: str,
        methodology_version: str,
        region: str | None = None,
        hardware: str | None = None,
        as_of: date | None = None,
    ) -> MethodologyFactor | None:
        candidates = await self._load_candidates(
            metric=metric,
            modality=modality,
            activity_type=activity_type,
            methodology_version=methodology_version,
            as_of=as_of or date.today(),
        )
        if not candidates:
            return None

        predicates: list[Callable[[MethodologyFactor], bool]] = [
            lambda f: (
                f.provider == provider
                and f.model == model
                and f.region is not None
                and f.hardware is not None
                and (region is None or f.region == region)
                and (hardware is None or f.hardware == hardware)
            ),
            lambda f: f.provider == provider and f.model == model,
            lambda f: f.provider == provider and f.model is None,
            lambda f: f.provider is None and f.model == model,
            lambda f: f.provider is None and f.model is None,
        ]
        for predicate in predicates:
            for factor in candidates:
                if predicate(factor):
                    return factor
        return None

    async def _load_candidates(
        self,
        *,
        metric: str,
        modality: str,
        activity_type: str,
        methodology_version: str,
        as_of: date,
    ) -> list[MethodologyFactor]:
        stmt = select(MethodologyFactor).where(
            MethodologyFactor.metric == metric,
            MethodologyFactor.modality == modality,
            MethodologyFactor.activity_type == activity_type,
            MethodologyFactor.methodology_version == methodology_version,
            MethodologyFactor.effective_from <= as_of,
        )
        result = await self._db.execute(stmt)
        rows = result.scalars().all()
        return [f for f in rows if f.effective_to is None or f.effective_to >= as_of]
