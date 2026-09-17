from datetime import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import decode_cursor, encode_cursor
from app.models.workload import AIWorkload

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


class WorkloadHistoryService:
    """Backs GET /v1/workloads and GET /v1/workloads/{id}.

    Ordering is always created_at DESC, id DESC (a stable, deterministic
    order even when many rows share the same created_at) and pagination
    is cursor-based (never offset) so results stay correct as new
    workloads are inserted between page fetches.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_organization(
        self,
        organization_id: str,
        *,
        project_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[AIWorkload], str | None]:
        limit = max(1, min(limit, MAX_PAGE_SIZE))

        stmt = select(AIWorkload).where(AIWorkload.organization_id == organization_id)
        if project_id is not None:
            stmt = stmt.where(AIWorkload.project_id == project_id)
        if provider is not None:
            stmt = stmt.where(AIWorkload.provider == provider)
        if model is not None:
            stmt = stmt.where(AIWorkload.model == model)
        if activity_type is not None:
            stmt = stmt.where(AIWorkload.activity_type == activity_type)
        if from_timestamp is not None:
            stmt = stmt.where(AIWorkload.timestamp >= from_timestamp)
        if to_timestamp is not None:
            stmt = stmt.where(AIWorkload.timestamp <= to_timestamp)

        if cursor is not None:
            cursor_created_at, cursor_id = decode_cursor(cursor)
            stmt = stmt.where(
                tuple_(AIWorkload.created_at, AIWorkload.id) < (cursor_created_at, cursor_id)
            )

        stmt = stmt.order_by(AIWorkload.created_at.desc(), AIWorkload.id.desc()).limit(limit + 1)

        rows = list((await self._db.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        items = rows[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

        return items, next_cursor

    async def get_owned(
        self, organization_id: str, workload_id: str, *, project_id: str | None = None
    ) -> AIWorkload:
        """Fetches a single workload scoped to organization_id and,
        when the caller holds a project-scoped key, also to project_id -
        the same rule list_for_organization applies, so a project-scoped
        key can never read another project's workload even within the
        same organization (sprint 2 follow-up review, item 1).
        """
        conditions = [AIWorkload.id == workload_id, AIWorkload.organization_id == organization_id]
        if project_id is not None:
            conditions.append(AIWorkload.project_id == project_id)
        result = await self._db.execute(select(AIWorkload).where(*conditions))
        workload = result.scalar_one_or_none()
        if workload is None:
            raise NotFoundError("Workload not found.")
        return workload
