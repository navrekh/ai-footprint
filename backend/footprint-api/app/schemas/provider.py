from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProviderRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "openai",
                "name": "OpenAI",
                "status": "active",
                "supported_modalities": ["text", "image", "audio", "coding"],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        },
    )

    id: str
    name: str
    status: str
    supported_modalities: list[str]
    created_at: datetime
    updated_at: datetime
