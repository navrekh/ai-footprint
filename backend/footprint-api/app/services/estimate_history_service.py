from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.estimate import Estimate
from app.models.workload import AIWorkload


class EstimateHistoryService:
    """Backs GET /v1/estimates/{estimate_id}.

    Tenant ownership is enforced by joining through the parent workload's
    organization_id (and, for a project-scoped key, project_id too),
    since Estimate itself does not carry either directly - it is scoped
    entirely through its workload.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_owned(
        self, organization_id: str, estimate_id: str, *, project_id: str | None = None
    ) -> Estimate:
        """A project-scoped key must never read an estimate belonging to
        another project, even within the same organization (sprint 2
        follow-up review, item 1) - mirrors WorkloadHistoryService.get_owned.
        """
        conditions = [Estimate.id == estimate_id, AIWorkload.organization_id == organization_id]
        if project_id is not None:
            conditions.append(AIWorkload.project_id == project_id)
        result = await self._db.execute(
            select(Estimate)
            .join(AIWorkload, AIWorkload.id == Estimate.workload_id)
            .where(*conditions)
        )
        estimate = result.scalar_one_or_none()
        if estimate is None:
            raise NotFoundError("Estimate not found.")
        return estimate
