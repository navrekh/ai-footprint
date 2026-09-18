from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "CI Key", "project_id": "proj_01hxyzabc123"}}
    )

    name: str = Field(min_length=1, max_length=255)
    project_id: str | None = Field(
        default=None,
        description=(
            "Scope the key to one project within the caller's organization. "
            "Omit to create an organization-level key."
        ),
    )
    expires_at: datetime | None = None


class ApiKeyCreated(BaseModel):
    """Returned exactly once, at creation time. The raw key is never
    retrievable again - only its hash and prefix are stored.
    """

    id: str
    key: str
    key_prefix: str
    name: str


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    project_id: str | None
    key_prefix: str
    name: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyRead]
    total: int
