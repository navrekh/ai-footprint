from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=1, max_length=255)


class ApiKeyCreated(BaseModel):
    """Returned exactly once, at creation time. The raw key is never retrievable again."""

    id: str
    raw_key: str
    key_prefix: str
    name: str


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    key_prefix: str
    name: str
    status: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None
