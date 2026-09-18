import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.config import get_settings
from app.core.errors import ErrorCode, InvalidRequestError
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.auth_service import AuthContext
from app.services.comparison_service import ComparisonService

router = APIRouter()


@router.post(
    "/compare",
    response_model=CompareResponse,
    tags=["resource-intelligence"],
    summary="Compare one workload definition across multiple provider/model candidates",
    description=(
        "Runs the same workload independently through each candidate's provider/model via "
        "the normal estimation pipeline - candidates are never aggregated, averaged, or "
        "ranked, and the response never declares a winner. A single candidate's failure "
        "(e.g. an unknown model) is reported for that candidate only, as `status: \"failed\"` "
        "in `results`, and never fails the whole request. Requires a valid API key, but "
        "touches no tenant-owned data and accepts no `organization_id`/`project_id`."
    ),
    responses=error_responses(*AUTH_ERRORS, ErrorCode.INVALID_REQUEST),
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
