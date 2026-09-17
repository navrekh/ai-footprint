import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.methodology.dto import EstimateResult
from app.methodology.pipeline import EstimationPipeline
from app.schemas.common import MetricRange
from app.schemas.estimate import EstimateResponse
from app.schemas.workload import WorkloadInput


def build_estimate_response(result: EstimateResult) -> EstimateResponse:
    return EstimateResponse(
        estimate_id=f"est_{uuid.uuid4().hex}",
        energy=MetricRange(
            status=result.energy.status,
            min=result.energy.min,
            max=result.energy.max,
            unit=result.energy.unit,
        ),
        water=MetricRange(
            status=result.water.status,
            min=result.water.min,
            max=result.water.max,
            unit=result.water.unit,
        ),
        carbon=MetricRange(
            status=result.carbon.status,
            min=result.carbon.min,
            max=result.carbon.max,
            unit=result.carbon.unit,
        ),
        confidence=result.confidence,
        evidence_level=result.evidence_level,
        accounting_boundary=result.accounting_boundary,
        methodology_version=result.methodology_version,
        assumptions=result.assumptions,
        created_at=datetime.now(UTC),
    )


class EstimateService:
    """Backs POST /v1/estimate: a stateless calculate-only endpoint - no
    AIWorkload or Estimate row is persisted (see README "Architecture
    notes" for why this differs from /v1/events).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._pipeline = EstimationPipeline(db)

    async def estimate(self, workload: WorkloadInput) -> EstimateResponse:
        result = await self._pipeline.run(workload)
        return build_estimate_response(result)
