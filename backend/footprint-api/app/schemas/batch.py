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


class AggregateImpact(BaseModel):
    energy: MetricRange
    water: MetricRange
    carbon: MetricRange


class BatchEstimateResponse(BaseModel):
    batch_id: str
    total_workloads: int
    successful_estimates: int
    failed_estimates: int
    aggregate_impact: AggregateImpact
    results: list[BatchItemResult]
