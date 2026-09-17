from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MethodologyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    description: str
    effective_date: date
    sources: list[str]
    assumptions: list[str]
    limitations: list[str]
    created_at: datetime
