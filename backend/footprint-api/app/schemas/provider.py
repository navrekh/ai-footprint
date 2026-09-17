from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    supported_modalities: list[str]
    created_at: datetime
    updated_at: datetime
