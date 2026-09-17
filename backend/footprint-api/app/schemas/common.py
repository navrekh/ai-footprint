from pydantic import BaseModel, Field

from app.models.enums import Confidence, MetricStatus


class MetricRange(BaseModel):
    status: MetricStatus
    min: float | None = Field(default=None)
    max: float | None = Field(default=None)
    unit: str


class AggregateMetricRange(MetricRange):
    """A metric range aggregated across multiple workloads that exposes
    completeness - shared by batch estimation (app/schemas/batch.py) and
    usage intelligence (app/schemas/usage.py).

    status is "ok" only when every contributing workload had a measured
    value for this metric; "partial" when some did and some did not
    (min/max sum only the measured ones); and "insufficient_data" when
    none did. A partial aggregate must never be indistinguishable from a
    complete one.
    """

    total_workloads: int
    measured_workloads: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


__all__ = [
    "MetricRange",
    "AggregateMetricRange",
    "ErrorDetail",
    "ErrorResponse",
    "Confidence",
]
