from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
