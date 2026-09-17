from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Confidence
from app.schemas.common import MetricRange


class EstimateResponse(BaseModel):
    """Stateless estimate response (POST /v1/estimate, /v1/batch-estimate items)."""

    estimate_id: str
    energy: MetricRange
    water: MetricRange
    carbon: MetricRange
    confidence: Confidence | None
    evidence_level: int | None
    accounting_boundary: str | None
    methodology_version: str | None
    assumptions: list[str]
    created_at: datetime


class PersistedEstimateRead(BaseModel):
    """A persisted estimate (GET /v1/estimates/{estimate_id}) - adds the
    provenance fields that only exist once an estimate is durably stored.
    """

    estimate_id: str
    workload_id: str
    provider: str | None
    model: str | None
    model_version: str | None
    energy: MetricRange
    water: MetricRange
    carbon: MetricRange
    confidence: Confidence | None
    evidence_level: int | None
    accounting_boundary: str | None
    methodology_version: str | None
    assumptions: list[str]
    status: str  # "measured" | "partial" | "insufficient_data"
    created_at: datetime
