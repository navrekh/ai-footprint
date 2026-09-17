import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.config import get_settings
from app.core.errors import InvalidRequestError
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.auth_service import AuthContext
from app.services.comparison_service import ComparisonService

router = APIRouter()


@router.post(
    "/compare",
    response_model=CompareResponse,
    tags=["resource-intelligence"],
    summary="Compare one workload definition across multiple provider/model candidates",
)
async def compare_workload(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> CompareResponse:
    del auth  # authentication required, but comparison reads no tenant-owned data
    settings = get_settings()
    if len(payload.candidates) > settings.MAX_COMPARE_CANDIDATES:
        raise InvalidRequestError(
            f"candidates exceeds the maximum of {settings.MAX_COMPARE_CANDIDATES}."
        )

    base_fields = payload.model_dump(exclude={"candidates"})
    results = await ComparisonService(db).compare(base_fields, payload.candidates)
    return CompareResponse(
        comparison_id=f"cmp_{uuid.uuid4().hex}",
        modality=payload.modality,
        activity_type=payload.activity_type,
        results=results,
    )
