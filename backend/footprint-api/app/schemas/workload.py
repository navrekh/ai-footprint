from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ActivityType, ClientType, Modality, validate_activity_type_modality


class ClientContext(BaseModel):
    """Identifies the software surface that instrumented a workload -
    distinct from `application_id` (see EventCreateRequest), which
    identifies the product/service/environment that *owns* the workload
    (Sprint 6 FRD section 38.2/38.3).

    Every field is optional and purely observational: nothing here is
    read by validation, provider/model/methodology resolution, or the
    estimation pipeline (app/methodology/pipeline.py), so submitting
    different client metadata for an otherwise identical workload never
    changes the resulting estimate. Treat every field as
    potentially user-controlled input, never as authorization data - it
    must never be used to derive organization/project/application
    ownership or API-key scope.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_type": "python_sdk",
                "client_name": "aifootprint-python",
                "client_version": "0.5.0",
                "integration_type": "backend_middleware",
                "integration_version": "1.2.0",
                "runtime": "python/3.13",
            }
        }
    )

    client_type: ClientType | None = Field(
        default=None,
        description="Controlled client-surface category. See ClientType for the full taxonomy.",
    )
    client_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Human-readable client/integration identifier, e.g. an SDK or app name.",
    )
    client_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description=(
            "Version of the client surface itself. Observational only - a client version "
            "change never implies an API version change and never alters estimation."
        ),
    )
    integration_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Free-form integration mechanism/category, e.g. 'backend_middleware'.",
    )
    integration_version: str | None = Field(default=None, min_length=1, max_length=32)
    runtime: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Optional non-sensitive runtime identifier, e.g. 'python/3.13'.",
    )


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
    client: ClientContext | None = Field(
        default=None,
        description=(
            "Optional client/integration metadata identifying the software surface that "
            "instrumented this workload (Sprint 6). Purely observational: never affects "
            "provider/model resolution, methodology resolution, or the resulting estimate."
        ),
    )

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
                "event_id": "evt_01hxyzabc123",
                "workload_id": "evt_01hxyzabc123",
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
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "evt_01hxyzabc123",
                "organization_id": "org_01hxyzabc123",
                "project_id": "proj_01hxyzabc123",
                "application_id": "app_01hxyzabc123",
                "provider": "openai",
                "model": "model-id",
                "model_version": "2026-01-01",
                "modality": "text",
                "activity_type": "text_generation",
                "timestamp": "2026-01-01T00:00:00Z",
                "input_tokens": 2000,
                "output_tokens": 1000,
                "input_characters": None,
                "output_characters": None,
                "image_count": None,
                "image_width": None,
                "image_height": None,
                "video_seconds": None,
                "video_resolution": None,
                "audio_seconds": None,
                "tool_calls": None,
                "duration_seconds": None,
                "duration_ms": None,
                "parent_workload_id": None,
                "metadata": None,
                "client": None,
                "created_at": "2026-01-01T00:00:00Z",
            }
        },
    )

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
    client: ClientContext | None = Field(validation_alias="client_context", default=None)
    created_at: datetime


class WorkloadPage(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "evt_01hxyzabc123",
                        "organization_id": "org_01hxyzabc123",
                        "project_id": "proj_01hxyzabc123",
                        "application_id": "app_01hxyzabc123",
                        "provider": "openai",
                        "model": "model-id",
                        "model_version": "2026-01-01",
                        "modality": "text",
                        "activity_type": "text_generation",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "input_tokens": 2000,
                        "output_tokens": 1000,
                        "input_characters": None,
                        "output_characters": None,
                        "image_count": None,
                        "image_width": None,
                        "image_height": None,
                        "video_seconds": None,
                        "video_resolution": None,
                        "audio_seconds": None,
                        "tool_calls": None,
                        "duration_seconds": None,
                        "duration_ms": None,
                        "parent_workload_id": None,
                        "metadata": None,
                        "client": None,
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ],
                "next_cursor": "MjAyNi0wMS0wMVQwMDowMDowMFp8ZXZ0XzAxaHh5emFiYzEyMw==",
            }
        }
    )

    items: list[WorkloadRead]
    next_cursor: str | None = None
