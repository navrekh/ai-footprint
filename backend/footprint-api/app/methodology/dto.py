from dataclasses import dataclass, field

from app.models.enums import Confidence, MetricStatus


@dataclass
class MetricEstimate:
    status: MetricStatus
    unit: str
    min: float | None = None
    max: float | None = None
    confidence: Confidence | None = None
    evidence_level: int | None = None
    accounting_boundary: str | None = None
    factor_id: str | None = None
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    # Completeness bookkeeping, populated by UncertaintyEngine.aggregate().
    # For a single (non-aggregated) workload these are always 1/1 or 1/0.
    total_workloads: int = 1
    measured_workloads: int = 0


@dataclass
class EstimateResult:
    energy: MetricEstimate
    water: MetricEstimate
    carbon: MetricEstimate
    confidence: Confidence | None
    evidence_level: int | None
    accounting_boundary: str | None
    methodology_version: str | None
    assumptions: list[str]
    # The canonical resolved provider/model/version actually used for this
    # calculation (may differ cosmetically from the raw request, e.g.
    # provider id normalization) - persisted onto Estimate for provenance.
    provider: str
    model: str
    model_version: str | None = None
