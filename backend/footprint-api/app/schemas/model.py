from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ModelRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "model_01hxyzabc123",
                "provider_id": "openai",
                "name": "model-id",
                "version": "2026-01-01",
                "modalities": ["text"],
                "status": "active",
                "methodology_version": "0.1",
                "effective_from": "2026-01-01",
                "effective_to": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        },
    )

    id: str
    provider_id: str
    name: str
    version: str | None
    modalities: list[str]
    status: str
    methodology_version: str | None
    effective_from: date | None
    effective_to: date | None
    created_at: datetime
    updated_at: datetime
