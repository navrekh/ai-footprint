from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ActivityType, Modality
from app.schemas.common import ComparisonCandidate
from app.schemas.compare import ComparisonResultItem


class BenchmarkDefinitionRead(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "benchmark_id": "text_generation_standard",
                "version": "1.0",
                "name": "Standard text generation",
                "description": "A representative conversational text-generation exchange.",
                "activity_type": "text_generation",
                "modality": "text",
                "parameters": {"input_tokens": 500, "output_tokens": 500},
            }
        }
    )

    benchmark_id: str
    version: str
    name: str
    description: str
    activity_type: ActivityType
    modality: Modality
    parameters: dict


class BenchmarkListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "benchmark_id": "text_generation_standard",
                        "version": "1.0",
                        "name": "Standard text generation",
                        "description": "A representative conversational text-generation exchange.",
                        "activity_type": "text_generation",
                        "modality": "text",
                        "parameters": {"input_tokens": 500, "output_tokens": 500},
                    }
                ],
                "total": 1,
            }
        }
    )

    items: list[BenchmarkDefinitionRead]
    total: int


class BenchmarkRunRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "benchmark_id": "text_generation_standard",
                "candidates": [
                    {"provider": "openai", "model": "model-id"},
                    {"provider": "anthropic", "model": "model-id"},
                ],
            }
        }
    )

    benchmark_id: str
    candidates: list[ComparisonCandidate] = Field(min_length=2)


class BenchmarkRunResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "benchmark_id": "text_generation_standard",
                "benchmark_version": "1.0",
                "modality": "text",
                "activity_type": "text_generation",
                "results": [
                    {
                        "candidate": {
                            "provider": "openai",
                            "model": "model-id",
                            "model_version": None,
                        },
                        "status": "success",
                        "resolved": {
                            "provider": "openai",
                            "model": "model-id",
                            "model_version": "2026-01-01",
                        },
                        "estimate": {
                            "estimate_id": "est_01hxyzabc123",
                            "energy": {"status": "ok", "min": 0.08, "max": 0.11, "unit": "Wh"},
                            "water": {"status": "ok", "min": 0.07, "max": 0.09, "unit": "mL"},
                            "carbon": {"status": "ok", "min": 0.01, "max": 0.015, "unit": "gCO2e"},
                            "confidence": "medium",
                            "evidence_level": 3,
                            "accounting_boundary": "B",
                            "methodology_version": "0.1",
                            "assumptions": ["Location-based grid emissions factor."],
                            "created_at": "2026-01-01T00:00:00Z",
                        },
                        "normalized": None,
                        "error": None,
                    }
                ],
            }
        }
    )

    benchmark_id: str
    benchmark_version: str
    modality: Modality
    activity_type: ActivityType
    results: list[ComparisonResultItem]
