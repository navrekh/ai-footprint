from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
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
)
async def create_estimate(
    payload: WorkloadInput,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> EstimateResponse:
    del auth  # authentication required, but not otherwise used by this stateless endpoint
    return await EstimateService(db).estimate(payload)
