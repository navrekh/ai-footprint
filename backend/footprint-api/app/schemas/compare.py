from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ActivityType, Modality, validate_activity_type_modality
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "modality": "text",
                "activity_type": "text_generation",
                "input_tokens": 2000,
                "output_tokens": 1000,
                "candidates": [
                    {"provider": "openai", "model": "model-id"},
                    {"provider": "anthropic", "model": "model-id"},
                ],
            }
        }
    )

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

    @model_validator(mode="after")
    def check_activity_matches_modality(self) -> "CompareRequest":
        """Rejects an incompatible activity_type/modality pair for the
        shared workload definition at request-validation time (422),
        reusing WorkloadInput's own validation function rather than a
        duplicated rule. This must happen here, not per-candidate: a
        malformed shared workload is a request-level error, not an
        individual candidate's failure, so it must never surface as
        HTTP 200 with every candidate independently reporting the same
        failure.
        """
        validate_activity_type_modality(self.activity_type, self.modality)
        return self


class ComparisonResultItem(BaseModel):
    """One candidate's independent outcome, shared by CompareResponse and
    BenchmarkRunResponse. Candidates are never aggregated or ranked
    against each other - this schema deliberately has no winner/best/
    score/ranking field of any kind (ARCHITECTURE.md ADR-008).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "candidate": {"provider": "openai", "model": "model-id", "model_version": None},
                "status": "success",
                "resolved": {
                    "provider": "openai",
                    "model": "model-id",
                    "model_version": "2026-01-01",
                },
                "estimate": {
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
                },
                "normalized": {
                    "denominator": {
                        "value": 3.0,
                        "unit": "1K tokens",
                        "basis": "input_plus_output",
                    },
                    "energy": {
                        "status": "ok",
                        "min": 0.1033,
                        "max": 0.14,
                        "unit": "Wh per 1K tokens",
                        "confidence": "medium",
                        "evidence_level": 3,
                        "methodology_version": "0.1",
                        "accounting_boundary": "B",
                    },
                    "water": {
                        "status": "ok",
                        "min": 0.0933,
                        "max": 0.1166,
                        "unit": "mL per 1K tokens",
                        "confidence": "medium",
                        "evidence_level": 3,
                        "methodology_version": "0.1",
                        "accounting_boundary": "B",
                    },
                    "carbon": {
                        "status": "ok",
                        "min": 0.0133,
                        "max": 0.02,
                        "unit": "gCO2e per 1K tokens",
                        "confidence": "medium",
                        "evidence_level": 3,
                        "methodology_version": "0.1",
                        "accounting_boundary": "B",
                    },
                },
                "error": None,
            }
        }
    )

    candidate: ComparisonCandidate  # as requested - model_version may be None
    status: str  # "success" | "failed"
    # The actual provider/model/model_version the estimate was computed
    # for, from EstimateResult - set on success even when the candidate
    # omitted model_version and ModelResolver resolved an active version.
    resolved: ComparisonCandidate | None = None
    estimate: EstimateResponse | None = None
    normalized: NormalizedResourceIntensity | None = None
    error: ErrorDetail | None = None


class CompareResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comparison_id": "cmp_01hxyzabc123",
                "modality": "text",
                "activity_type": "text_generation",
                "results": [
                    {
                        "candidate": {
                            "provider": "openai",
                            "model": "model-id",
                            "model_version": None,
                        },
                        "status": "success",
                        "resolved": {
                            "provider": "openai",
                            "model": "model-id",
                            "model_version": "2026-01-01",
                        },
                        "estimate": {
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
                        },
                        "normalized": None,
                        "error": None,
                    },
                    {
                        "candidate": {
                            "provider": "anthropic",
                            "model": "model-id",
                            "model_version": None,
                        },
                        "status": "failed",
                        "resolved": None,
                        "estimate": None,
                        "normalized": None,
                        "error": {
                            "code": "MODEL_NOT_FOUND",
                            "message": "Model 'model-id' was not found for provider 'anthropic'.",
                            "request_id": "req_0123456789abcdef0123456789abcdef",
                        },
                    },
                ],
            }
        }
    )

    comparison_id: str
    modality: Modality
    activity_type: ActivityType
    results: list[ComparisonResultItem]
