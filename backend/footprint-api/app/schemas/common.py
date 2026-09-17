from pydantic import BaseModel, Field

from app.models.enums import Confidence, MetricStatus, NormalizationBasis


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


class Denominator(BaseModel):
    """The workload quantity a normalized resource-intensity range was
    divided by - always returned alongside the normalized value so the
    calculation is auditable (docs/METHODOLOGY.md section 25).
    """

    value: float
    unit: str
    basis: NormalizationBasis


class NormalizedMetricRange(BaseModel):
    """A resource-intensity range expressed relative to a workload
    quantity (e.g. energy per 1,000 tokens), rather than absolute Wh/mL/
    gCO2e for the whole workload.

    Derived by dividing an existing MetricRange's min/max independently
    by a Denominator - never averaged into a point value - and always
    carries the same status/confidence/evidence_level/methodology_version/
    accounting_boundary as the raw estimate it was computed from.
    Normalization never grants a metric more certainty than the raw
    estimate already had: an insufficient_data raw metric normalizes to
    an insufficient_data range with min/max absent, never to zero.
    """

    status: MetricStatus
    min: float | None = Field(default=None)
    max: float | None = Field(default=None)
    unit: str
    confidence: Confidence | None = None
    evidence_level: int | None = None
    methodology_version: str | None = None
    accounting_boundary: str | None = None


class NormalizedResourceIntensity(BaseModel):
    """Normalized energy/water/carbon for one comparison/benchmark result
    item, sharing a single Denominator since the denominator is a
    property of the workload, not of any individual metric.
    """

    denominator: Denominator
    energy: NormalizedMetricRange | None = None
    water: NormalizedMetricRange | None = None
    carbon: NormalizedMetricRange | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ComparisonCandidate(BaseModel):
    """One provider/model target to estimate the same workload against -
    shared by POST /v1/compare and POST /v1/benchmarks/run (sprint 4 FRD
    section 35.2).
    """

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    model_version: str | None = None


__all__ = [
    "MetricRange",
    "AggregateMetricRange",
    "Denominator",
    "NormalizedMetricRange",
    "NormalizedResourceIntensity",
    "ComparisonCandidate",
    "ErrorDetail",
    "ErrorResponse",
    "Confidence",
]
