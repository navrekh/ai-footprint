from pydantic import BaseModel, Field

from app.models.enums import ActivityType, Modality
from app.schemas.common import ComparisonCandidate, ErrorDetail, NormalizedResourceIntensity
from app.schemas.estimate import EstimateResponse


class CompareRequest(BaseModel):
    """One workload definition (the same optional-quantity fields as
    WorkloadInput, minus provider/model/model_version, which come from
    each candidate instead) plus the provider/model candidates to
    evaluate it against independently (sprint 4 FRD section 35.2).

    provider/model/model_version are intentionally not accepted here -
    they belong exclusively to `candidates`, so there is no ambiguous or
    redundant top-level provider/model field a caller could set
    inconsistently with their candidate list.
    """

    modality: Modality
    activity_type: ActivityType

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    input_characters: int | None = Field(default=None, ge=0)
    output_characters: int | None = Field(default=None, ge=0)

    image_count: int | None = Field(default=None, ge=0)
    image_width: int | None = Field(default=None, ge=0)
    image_height: int | None = Field(default=None, ge=0)

    video_seconds: float | None = Field(default=None, ge=0)
    video_resolution: str | None = None

    audio_seconds: float | None = Field(default=None, ge=0)

    tool_calls: int | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    duration_ms: float | None = Field(default=None, ge=0)

    metadata: dict | None = None

    candidates: list[ComparisonCandidate] = Field(min_length=2)


class ComparisonResultItem(BaseModel):
    """One candidate's independent outcome, shared by CompareResponse and
    BenchmarkRunResponse. Candidates are never aggregated or ranked
    against each other - this schema deliberately has no winner/best/
    score/ranking field of any kind (ARCHITECTURE.md ADR-008).
    """

    candidate: ComparisonCandidate
    status: str  # "success" | "failed"
    estimate: EstimateResponse | None = None
    normalized: NormalizedResourceIntensity | None = None
    error: ErrorDetail | None = None


class CompareResponse(BaseModel):
    comparison_id: str
    modality: Modality
    activity_type: ActivityType
    results: list[ComparisonResultItem]
