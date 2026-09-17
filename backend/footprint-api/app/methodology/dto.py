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
