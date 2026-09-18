from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.errors import ErrorCode
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.schemas.estimate import EstimateResponse
from app.schemas.workload import WorkloadInput
from app.services.auth_service import AuthContext
from app.services.estimate_service import EstimateService

router = APIRouter()


@router.post(
    "/estimate",
    response_model=EstimateResponse,
    tags=["estimation"],
    summary="Calculate a single workload estimate (stateless, not persisted)",
    description=(
        "Runs the full estimation pipeline for one workload and returns the result "
        "immediately - nothing is written to the database. A valid API key is required, "
        "but the request touches no tenant-owned data. If no approved methodology factor "
        "exists, the response reports `insufficient_data` rather than a fabricated value."
    ),
    responses=error_responses(
        *AUTH_ERRORS,
        ErrorCode.PROVIDER_NOT_FOUND,
        ErrorCode.MODEL_NOT_FOUND,
        ErrorCode.MODEL_NOT_SUPPORTED,
        ErrorCode.INVALID_WORKLOAD,
    ),
)
async def create_estimate(
    payload: WorkloadInput,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> EstimateResponse:
    del auth  # authentication required, but not otherwise used by this stateless endpoint
    return await EstimateService(db).estimate(payload)
