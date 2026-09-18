from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationEnvironment, ApplicationStatus


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Customer Support Bot",
                "description": "Support chat assistant",
                "environment": "production",
            }
        }
    )

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    environment: ApplicationEnvironment | None = None
    project_id: str | None = Field(
        default=None,
        description=(
            "Target project. Required when authenticating with an organization-level API "
            "key; optional (and must match the key's own project) for a project-scoped key."
        ),
    )


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "inactive", "description": "Deprecated"}}
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: ApplicationStatus | None = None
    environment: ApplicationEnvironment | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "app_01hxyzabc123",
                "project_id": "proj_01hxyzabc123",
                "name": "Customer Support Bot",
                "slug": "customer-support-bot",
                "description": "Support chat assistant",
                "status": "active",
                "environment": "production",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        },
    )

    id: str
    project_id: str
    name: str
    slug: str
    description: str | None
    status: str
    environment: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "app_01hxyzabc123",
                        "project_id": "proj_01hxyzabc123",
                        "name": "Customer Support Bot",
                        "slug": "customer-support-bot",
                        "description": "Support chat assistant",
                        "status": "active",
                        "environment": "production",
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ],
                "total": 1,
            }
        }
    )

    items: list[ApplicationRead]
    total: int
