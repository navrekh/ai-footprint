from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.config import get_settings
from app.core.errors import BenchmarkNotFoundError, ErrorCode, InvalidRequestError
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.methodology.benchmarks import BenchmarkDefinition, get_benchmark, list_benchmarks
from app.models.enums import ActivityType, Modality
from app.schemas.benchmark import (
    BenchmarkDefinitionRead,
    BenchmarkListResponse,
    BenchmarkRunRequest,
    BenchmarkRunResponse,
)
from app.services.auth_service import AuthContext
from app.services.comparison_service import ComparisonService

router = APIRouter()


def _to_read(definition: BenchmarkDefinition) -> BenchmarkDefinitionRead:
    return BenchmarkDefinitionRead(
        benchmark_id=definition.benchmark_id,
        version=definition.version,
        name=definition.name,
        description=definition.description,
        activity_type=definition.activity_type,
        modality=definition.modality,
        parameters=definition.parameters,
    )


@router.get(
    "/benchmarks",
    response_model=BenchmarkListResponse,
    tags=["resource-intelligence"],
    summary="List standardized benchmark workload definitions (public reference data)",
    description=(
        "Public, no authentication required - static, versioned, deterministically-ordered "
        "definitions, consistent with `GET /v1/providers`/`/v1/models`/`/v1/methodology`."
    ),
)
async def list_benchmark_definitions(
    activity_type: ActivityType | None = Query(default=None),
    modality: Modality | None = Query(default=None),
) -> BenchmarkListResponse:
    definitions = list_benchmarks(activity_type=activity_type, modality=modality)
    items = [_to_read(definition) for definition in definitions]
    return BenchmarkListResponse(items=items, total=len(items))


@router.get(
    "/benchmarks/{benchmark_id}",
    response_model=BenchmarkDefinitionRead,
    tags=["resource-intelligence"],
    summary="Return one benchmark definition (public reference data)",
    description="Public, no authentication required.",
    responses=error_responses(ErrorCode.BENCHMARK_NOT_FOUND),
)
async def get_benchmark_definition(benchmark_id: str) -> BenchmarkDefinitionRead:
    definition = get_benchmark(benchmark_id)
    if definition is None:
        raise BenchmarkNotFoundError(f"Benchmark '{benchmark_id}' was not found.")
    return _to_read(definition)


@router.post(
    "/benchmarks/run",
    response_model=BenchmarkRunResponse,
    tags=["resource-intelligence"],
    summary="Execute a benchmark definition against multiple provider/model candidates",
    description=(
        "Looks up the named static benchmark definition, then runs it through the same "
        "internal mechanism as `POST /v1/compare` - no second estimation path exists. May "
        "legitimately return `insufficient_data` for a candidate rather than a fabricated "
        "value. Requires a valid API key; touches no tenant-owned data."
    ),
    responses=error_responses(
        *AUTH_ERRORS, ErrorCode.INVALID_REQUEST, ErrorCode.BENCHMARK_NOT_FOUND
    ),
)
async def run_benchmark(
    payload: BenchmarkRunRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> BenchmarkRunResponse:
    del auth  # authentication required, but benchmark execution reads no tenant-owned data
    settings = get_settings()
    if len(payload.candidates) > settings.MAX_COMPARE_CANDIDATES:
        raise InvalidRequestError(
            f"candidates exceeds the maximum of {settings.MAX_COMPARE_CANDIDATES}."
        )

    definition, results = await ComparisonService(db).run_benchmark(
        payload.benchmark_id, payload.candidates
    )
    return BenchmarkRunResponse(
        benchmark_id=definition.benchmark_id,
        benchmark_version=definition.version,
        modality=definition.modality,
        activity_type=definition.activity_type,
        results=results,
    )
