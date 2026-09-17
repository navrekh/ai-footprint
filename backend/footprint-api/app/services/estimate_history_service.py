from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.estimate import Estimate
from app.models.workload import AIWorkload


class EstimateHistoryService:
    """Backs GET /v1/estimates/{estimate_id}.

    Tenant ownership is enforced by joining through the parent workload's
    organization_id, since Estimate itself does not carry organization_id
    directly - it is scoped entirely through its workload.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_owned(self, organization_id: str, estimate_id: str) -> Estimate:
        result = await self._db.execute(
            select(Estimate)
            .join(AIWorkload, AIWorkload.id == Estimate.workload_id)
            .where(Estimate.id == estimate_id, AIWorkload.organization_id == organization_id)
        )
        estimate = result.scalar_one_or_none()
        if estimate is None:
            raise NotFoundError("Estimate not found.")
        return estimate
