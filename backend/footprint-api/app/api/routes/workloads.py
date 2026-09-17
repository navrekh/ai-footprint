from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.models.enums import ActivityType
from app.schemas.workload import WorkloadPage, WorkloadRead
from app.services.auth_service import AuthContext
from app.services.tenant_context import resolve_optional_project_filter
from app.services.workload_history_service import WorkloadHistoryService

router = APIRouter()


@router.get(
    "/workloads",
    response_model=WorkloadPage,
    tags=["workloads"],
    summary="List workload history for the authenticated tenant (cursor-paginated)",
)
async def list_workloads(
    project: str | None = Query(default=None, description="Filter by project id"),
    provider: str | None = Query(default=None, description="Filter by provider id"),
    model: str | None = Query(default=None, description="Filter by model name"),
    activity_type: ActivityType | None = Query(default=None),
    from_timestamp: datetime | None = Query(default=None, alias="from"),
    to_timestamp: datetime | None = Query(default=None, alias="to"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> WorkloadPage:
    project_filter = resolve_optional_project_filter(auth, project)
    items, next_cursor = await WorkloadHistoryService(db).list_for_organization(
        auth.organization.id,
        project_id=project_filter,
        provider=provider,
        model=model,
        activity_type=activity_type.value if activity_type else None,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        cursor=cursor,
        limit=limit,
    )
    return WorkloadPage(
        items=[WorkloadRead.model_validate(w) for w in items], next_cursor=next_cursor
    )


@router.get(
    "/workloads/{workload_id}",
    response_model=WorkloadRead,
    tags=["workloads"],
    summary="Get a single workload owned by the authenticated tenant",
)
async def get_workload(
    workload_id: str,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> WorkloadRead:
    workload = await WorkloadHistoryService(db).get_owned(auth.organization.id, workload_id)
    return WorkloadRead.model_validate(workload)
