from pydantic import BaseModel, Field

from app.schemas.common import ErrorDetail, MetricRange
from app.schemas.estimate import EstimateResponse
from app.schemas.workload import WorkloadInput


class BatchEstimateRequest(BaseModel):
    workloads: list[WorkloadInput] = Field(min_length=1)


class BatchItemResult(BaseModel):
    index: int
    status: str  # "success" | "failed"
    estimate: EstimateResponse | None = None
    error: ErrorDetail | None = None


class AggregateMetricRange(MetricRange):
    """A batch-aggregated metric range that exposes completeness.

    status is "ok" only when every successfully-estimated workload in the
    batch contributed a measured value for this metric; "partial" when
    some did and some did not (min/max sum only the measured ones); and
    "insufficient_data" when none did. A partial aggregate must never be
    indistinguishable from a complete one (sprint review, item 3).
    """

    total_workloads: int
    measured_workloads: int


class AggregateImpact(BaseModel):
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class BatchEstimateResponse(BaseModel):
    batch_id: str
    total_workloads: int
    successful_estimates: int
    failed_estimates: int
    aggregate_impact: AggregateImpact
    results: list[BatchItemResult]
