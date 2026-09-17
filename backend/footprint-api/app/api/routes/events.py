from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.schemas.workload import EventCreateRequest, EventCreateResponse
from app.services.auth_service import AuthContext
from app.services.workload_service import WorkloadService

router = APIRouter()


@router.post(
    "/events",
    response_model=EventCreateResponse,
    tags=["estimation"],
    summary="Persist a workload event and its associated estimate",
)
async def create_event(
    payload: EventCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> EventCreateResponse:
    workload, estimate = await WorkloadService(db).create_event(
        organization_id=auth.organization.id,
        project_id=auth.project.id,
        payload=payload,
    )
    return EventCreateResponse(event_id=workload.id, estimate_id=estimate.id)
