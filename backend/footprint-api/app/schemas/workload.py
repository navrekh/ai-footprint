from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ActivityType, Modality, validate_activity_type_modality


class WorkloadInput(BaseModel):
    """Shared request shape for /v1/estimate, /v1/events and /v1/batch-estimate items."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "provider": "openai",
                "model": "model-id",
                "modality": "text",
                "activity_type": "text_generation",
                "input_tokens": 2000,
                "output_tokens": 1000,
            }
        }
    )

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
        validate_activity_type_modality(self.activity_type, self.modality)
        return self


class EventCreateRequest(WorkloadInput):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "provider": "openai",
                "model": "model-id",
                "modality": "text",
                "activity_type": "text_generation",
                "input_tokens": 2000,
                "output_tokens": 1000,
                "project_id": "proj_01hxyzabc123",
                "application_id": "app_01hxyzabc123",
                "idempotency_key": "checkout-session-8f3e2c1a",
            }
        }
    )

    timestamp: datetime | None = None
    parent_workload_id: str | None = None
    project_id: str | None = Field(
        default=None,
        description=(
            "Target project. Required when authenticating with an organization-level API "
            "key; optional (and must match the key's own project) for a project-scoped key."
        ),
    )
    application_id: str | None = Field(
        default=None,
        description=(
            "Optional application within the target project. Must belong to the same "
            "project the event is being persisted under."
        ),
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description=(
            "Optional client-supplied key. Resubmitting the same idempotency_key for the "
            "same project returns the original workload/estimate instead of creating a "
            "duplicate measurement."
        ),
    )


class EventCreateResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "wl_01hxyzabc123",
                "workload_id": "wl_01hxyzabc123",
                "estimate_id": "est_01hxyzabc123",
                "status": "measured",
                "idempotent_replay": False,
            }
        }
    )

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
    application_id: str | None
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
