from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.errors import ErrorCode
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.methodology.event_status import compute_event_status
from app.models.enums import Confidence, MetricStatus
from app.models.estimate import Estimate
from app.schemas.common import MetricRange
from app.schemas.estimate import PersistedEstimateRead
from app.services.auth_service import AuthContext
from app.services.estimate_history_service import EstimateHistoryService
from app.services.tenant_context import resolve_optional_project_filter

router = APIRouter()


def _to_persisted_estimate_read(estimate: Estimate) -> PersistedEstimateRead:
    return PersistedEstimateRead(
        estimate_id=estimate.id,
        workload_id=estimate.workload_id,
        provider=estimate.provider,
        model=estimate.model,
        model_version=estimate.model_version,
        energy=MetricRange(
            status=MetricStatus(estimate.energy_status),
            min=estimate.energy_min_wh,
            max=estimate.energy_max_wh,
            unit="Wh",
        ),
        water=MetricRange(
            status=MetricStatus(estimate.water_status),
            min=estimate.water_min_ml,
            max=estimate.water_max_ml,
            unit="mL",
        ),
        carbon=MetricRange(
            status=MetricStatus(estimate.carbon_status),
            min=estimate.carbon_min_g,
            max=estimate.carbon_max_g,
            unit="gCO2e",
        ),
        confidence=Confidence(estimate.confidence) if estimate.confidence else None,
        evidence_level=estimate.evidence_level,
        accounting_boundary=estimate.accounting_boundary,
        methodology_version=estimate.methodology_version,
        assumptions=estimate.assumptions,
        status=compute_event_status(
            estimate.energy_status, estimate.water_status, estimate.carbon_status
        ),
        created_at=estimate.created_at,
    )


@router.get(
    "/estimates/{estimate_id}",
    response_model=PersistedEstimateRead,
    tags=["estimates"],
    summary="Get a persisted estimate owned by the authenticated tenant",
    description=(
        "Only estimates created via `POST /v1/events` are persisted and retrievable here - "
        "an `estimate_id` from the stateless `POST /v1/estimate` has no corresponding row."
    ),
    responses=error_responses(*AUTH_ERRORS, ErrorCode.NOT_FOUND),
)
async def get_estimate(
    estimate_id: str,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> PersistedEstimateRead:
    project_filter = resolve_optional_project_filter(auth, None)
    estimate = await EstimateHistoryService(db).get_owned(
        auth.organization.id, estimate_id, project_id=project_filter
    )
    return _to_persisted_estimate_read(estimate)
