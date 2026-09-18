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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "key_01hxyzabc123",
                "key": "afp_live_9f8c1b2a...(shown only this once)",
                "key_prefix": "afp_live_9f8c1b2a",
                "name": "CI Key",
            }
        }
    )

    id: str
    key: str
    key_prefix: str
    name: str


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "key_01hxyzabc123",
                "organization_id": "org_01hxyzabc123",
                "project_id": "proj_01hxyzabc123",
                "key_prefix": "afp_live_9f8c1b2a",
                "name": "CI Key",
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "expires_at": None,
                "last_used_at": "2026-01-02T00:00:00Z",
                "revoked_at": None,
            }
        },
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "key_01hxyzabc123",
                        "organization_id": "org_01hxyzabc123",
                        "project_id": "proj_01hxyzabc123",
                        "key_prefix": "afp_live_9f8c1b2a",
                        "name": "CI Key",
                        "status": "active",
                        "created_at": "2026-01-01T00:00:00Z",
                        "expires_at": None,
                        "last_used_at": "2026-01-02T00:00:00Z",
                        "revoked_at": None,
                    }
                ],
                "total": 1,
            }
        }
    )

    items: list[ApiKeyRead]
    total: int
