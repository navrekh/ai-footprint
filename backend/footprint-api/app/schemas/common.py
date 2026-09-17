from pydantic import BaseModel, Field

from app.models.enums import Confidence, MetricStatus


class MetricRange(BaseModel):
    status: MetricStatus
    min: float | None = Field(default=None)
    max: float | None = Field(default=None)
    unit: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


__all__ = ["MetricRange", "ErrorDetail", "ErrorResponse", "Confidence"]
