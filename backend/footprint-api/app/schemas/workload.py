from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ACTIVITY_TYPE_MODALITIES, ActivityType, Modality


class WorkloadInput(BaseModel):
    """Shared request shape for /v1/estimate, /v1/events and /v1/batch-estimate items."""

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    model_version: str | None = Field(
        default=None,
        description=(
            "Optional explicit model registry version. When omitted, the current active "
            "version is resolved deterministically (see ModelResolver)."
        ),
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

    @model_validator(mode="after")
    def check_activity_matches_modality(self) -> "WorkloadInput":
        allowed = ACTIVITY_TYPE_MODALITIES.get(self.activity_type)
        if allowed is not None and self.modality not in allowed:
            raise ValueError(
                f"activity_type '{self.activity_type}' is not valid for modality "
                f"'{self.modality}'"
            )
        return self


class EventCreateRequest(WorkloadInput):
    timestamp: datetime | None = None
    parent_workload_id: str | None = None
    project_id: str | None = Field(
        default=None,
        description=(
            "Target project. Required when authenticating with an organization-level API "
            "key; optional (and must match the key's own project) for a project-scoped key."
        ),
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional client-supplied key. Resubmitting the same idempotency_key for the "
            "same project returns the original workload/estimate instead of creating a "
            "duplicate measurement."
        ),
    )


class EventCreateResponse(BaseModel):
    event_id: str  # kept for Sprint 1 compatibility; identical to workload_id
    workload_id: str
    estimate_id: str
    status: str  # "measured" | "partial" | "insufficient_data"
    idempotent_replay: bool = False


class WorkloadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    project_id: str
    provider: str
    model: str
    model_version: str | None
    modality: str
    activity_type: str
    timestamp: datetime
    input_tokens: int | None
    output_tokens: int | None
    input_characters: int | None
    output_characters: int | None
    image_count: int | None
    image_width: int | None
    image_height: int | None
    video_seconds: float | None
    video_resolution: str | None
    audio_seconds: float | None
    tool_calls: int | None
    duration_seconds: float | None
    duration_ms: float | None
    parent_workload_id: str | None
    metadata: dict | None = Field(validation_alias="workload_metadata", default=None)
    created_at: datetime


class WorkloadPage(BaseModel):
    items: list[WorkloadRead]
    next_cursor: str | None = None
