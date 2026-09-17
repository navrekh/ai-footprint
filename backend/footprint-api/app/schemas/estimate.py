from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Confidence
from app.schemas.common import MetricRange


class EstimateResponse(BaseModel):
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
