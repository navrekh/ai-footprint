from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    slug: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int
