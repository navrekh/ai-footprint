from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.config import get_settings
from app.core.errors import ErrorCode, InvalidRequestError
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.schemas.batch import BatchEstimateRequest, BatchEstimateResponse
from app.services.auth_service import AuthContext
from app.services.batch_service import BatchService

router = APIRouter()


@router.post(
    "/batch-estimate",
    response_model=BatchEstimateResponse,
    tags=["estimation"],
    summary="Calculate a bounded batch of workload estimates (stateless, not persisted)",
    description=(
        "Stateless, bounded by `MAX_BATCH_SIZE`. A single invalid workload never fails the "
        "whole batch - each item's outcome (`success`/`failed`) is reported independently "
        "in `results`; only exceeding the batch-size bound itself is a request-level error."
    ),
    responses=error_responses(*AUTH_ERRORS, ErrorCode.INVALID_REQUEST),
)
async def batch_estimate(
    payload: BatchEstimateRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> BatchEstimateResponse:
    del auth
    settings = get_settings()
    if len(payload.workloads) > settings.MAX_BATCH_SIZE:
        raise InvalidRequestError(
            f"Batch size exceeds the maximum of {settings.MAX_BATCH_SIZE} workloads."
        )
    return await BatchService(db).run_batch(payload.workloads)
