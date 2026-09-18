from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.errors import ErrorCode
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.methodology.event_status import compute_event_status
from app.schemas.workload import EventCreateRequest, EventCreateResponse
from app.services.auth_service import AuthContext
from app.services.tenant_context import resolve_target_project_id
from app.services.workload_service import WorkloadService

router = APIRouter()


@router.post(
    "/events",
    response_model=EventCreateResponse,
    tags=["estimation"],
    summary="Persist a workload event and its associated estimate",
    description=(
        "Persists an `AIWorkload` and creates its `Estimate`. Supports an optional "
        "`idempotency_key`: resubmitting the same key for the same project returns the "
        "original `workload_id`/`estimate_id` (`idempotent_replay: true`) instead of "
        "creating a duplicate measurement. `application_id`, when supplied, must belong to "
        "the same project the event is persisted under."
    ),
    responses=error_responses(
        *AUTH_ERRORS,
        ErrorCode.FORBIDDEN,
        ErrorCode.MISSING_PARAMETER,
        ErrorCode.NOT_FOUND,
        ErrorCode.PROVIDER_NOT_FOUND,
        ErrorCode.MODEL_NOT_FOUND,
        ErrorCode.MODEL_NOT_SUPPORTED,
        ErrorCode.INVALID_WORKLOAD,
        ErrorCode.APPLICATION_NOT_FOUND,
        ErrorCode.APPLICATION_PROJECT_MISMATCH,
    ),
)
async def create_event(
    payload: EventCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> EventCreateResponse:
    project_id = await resolve_target_project_id(db, auth, payload.project_id)

    workload, estimate, is_replay = await WorkloadService(db).create_event(
        organization_id=auth.organization.id,
        project_id=project_id,
        payload=payload,
    )
    status = compute_event_status(
        estimate.energy_status, estimate.water_status, estimate.carbon_status
    )
    return EventCreateResponse(
        event_id=workload.id,
        workload_id=workload.id,
        estimate_id=estimate.id,
        status=status,
        idempotent_replay=is_replay,
    )
