from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Confidence
from app.schemas.common import MetricRange


class EstimateResponse(BaseModel):
    """Stateless estimate response (POST /v1/estimate, /v1/batch-estimate items)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estimate_id": "est_01hxyzabc123",
                "energy": {"status": "ok", "min": 0.31, "max": 0.42, "unit": "Wh"},
                "water": {"status": "ok", "min": 0.28, "max": 0.35, "unit": "mL"},
                "carbon": {"status": "ok", "min": 0.04, "max": 0.06, "unit": "gCO2e"},
                "confidence": "medium",
                "evidence_level": 3,
                "accounting_boundary": "B",
                "methodology_version": "0.1",
                "assumptions": ["Location-based grid emissions factor."],
                "created_at": "2026-01-01T00:00:00Z",
            }
        }
    )

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
