import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.request_id import get_request_id
from app.methodology.dto import MetricEstimate
from app.methodology.pipeline import EstimationPipeline
from app.methodology.uncertainty import UncertaintyEngine
from app.schemas.batch import AggregateImpact, BatchEstimateResponse, BatchItemResult
from app.schemas.common import ErrorDetail, MetricRange
from app.schemas.workload import WorkloadInput
from app.services.estimate_service import build_estimate_response


def _to_range(estimate: MetricEstimate) -> MetricRange:
    return MetricRange(
        status=estimate.status, min=estimate.min, max=estimate.max, unit=estimate.unit
    )


class BatchService:
    """Backs POST /v1/batch-estimate: a bounded, stateless batch calculate
    endpoint. A single invalid workload never corrupts the batch - each
    item's outcome is reported independently (sprint brief section 21).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._pipeline = EstimationPipeline(db)

    async def run_batch(self, workloads: list[WorkloadInput]) -> BatchEstimateResponse:
        results: list[BatchItemResult] = []
        energy_estimates: list[MetricEstimate] = []
        water_estimates: list[MetricEstimate] = []
        carbon_estimates: list[MetricEstimate] = []
        successful = 0
        failed = 0

        for index, workload in enumerate(workloads):
            try:
                result = await self._pipeline.run(workload)
            except AppError as exc:
                failed += 1
                results.append(
                    BatchItemResult(
                        index=index,
                        status="failed",
                        error=ErrorDetail(
                            code=exc.code.value,
                            message=exc.message,
                            request_id=get_request_id() or "",
                        ),
                    )
                )
                continue

            successful += 1
            energy_estimates.append(result.energy)
            water_estimates.append(result.water)
            carbon_estimates.append(result.carbon)
            results.append(
                BatchItemResult(
                    index=index, status="success", estimate=build_estimate_response(result)
                )
            )

        aggregate = AggregateImpact(
            energy=_to_range(UncertaintyEngine.aggregate(energy_estimates, "Wh")),
            water=_to_range(UncertaintyEngine.aggregate(water_estimates, "mL")),
            carbon=_to_range(UncertaintyEngine.aggregate(carbon_estimates, "gCO2e")),
        )

        return BatchEstimateResponse(
            batch_id=f"batch_{uuid.uuid4().hex}",
            total_workloads=len(workloads),
            successful_estimates=successful,
            failed_estimates=failed,
            aggregate_impact=aggregate,
            results=results,
        )
