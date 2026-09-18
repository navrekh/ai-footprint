from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MethodologyRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "methodology_01hxyzabc123",
                "version": "0.1",
                "description": "Initial AI Footprint estimation methodology.",
                "effective_date": "2026-01-01",
                "sources": ["https://example.org/methodology-whitepaper"],
                "assumptions": ["Location-based grid emissions factor."],
                "limitations": ["Does not account for embodied hardware impact."],
                "created_at": "2026-01-01T00:00:00Z",
            }
        },
    )

    id: str
    version: str
    description: str
    effective_date: date
    sources: list[str]
    assumptions: list[str]
    limitations: list[str]
    created_at: datetime
