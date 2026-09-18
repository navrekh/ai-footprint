from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.api_key import ApiKeyCreated
from app.schemas.project import ProjectRead


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"name": "Acme Inc"}})

    name: str = Field(min_length=1, max_length=255)


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime


class OrganizationBootstrapResponse(BaseModel):
    """Returned by POST /v1/organizations.

    Creating an organization has no prior authentication context to bind
    to (it is the signup step), so it also creates a default project and
    the organization's first API key in the same call - the only place a
    raw key is returned outside of POST /v1/api-keys.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organization": {
                    "id": "org_01hxyzabc123",
                    "name": "Acme Inc",
                    "slug": "acme-inc",
                    "status": "active",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                "project": {
                    "id": "proj_01hxyzabc123",
                    "organization_id": "org_01hxyzabc123",
                    "name": "Default Project",
                    "slug": "default-project",
                    "description": None,
                    "status": "active",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                "api_key": {
                    "id": "key_01hxyzabc123",
                    "key": "afp_live_9f8c1b2a...(shown only this once)",
                    "key_prefix": "afp_live_9f8c1b2a",
                    "name": "Default Key",
                },
            }
        }
    )

    organization: OrganizationRead
    project: ProjectRead
    api_key: ApiKeyCreated
