from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.api_key import ApiKeyCreated
from app.schemas.project import ProjectRead


class OrganizationCreate(BaseModel):
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

    organization: OrganizationRead
    project: ProjectRead
    api_key: ApiKeyCreated
