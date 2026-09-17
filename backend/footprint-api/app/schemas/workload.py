from datetime import datetime

from pydantic import BaseModel, Field, model_validator

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

    image_count: int | None = Field(default=None, ge=0)
    image_width: int | None = Field(default=None, ge=0)
    image_height: int | None = Field(default=None, ge=0)

    video_seconds: float | None = Field(default=None, ge=0)
    video_resolution: str | None = None

    audio_seconds: float | None = Field(default=None, ge=0)

    tool_calls: int | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)

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


class EventCreateResponse(BaseModel):
    event_id: str
    estimate_id: str
