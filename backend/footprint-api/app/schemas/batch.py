from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AggregateMetricRange, ErrorDetail
from app.schemas.estimate import EstimateResponse
from app.schemas.workload import WorkloadInput


class BatchEstimateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workloads": [
                    {
                        "provider": "openai",
                        "model": "model-id",
                        "modality": "text",
                        "activity_type": "text_generation",
                        "input_tokens": 2000,
                        "output_tokens": 1000,
                    },
                    {
                        "provider": "anthropic",
                        "model": "model-id",
                        "modality": "text",
                        "activity_type": "text_generation",
                        "input_tokens": 1500,
                        "output_tokens": 800,
                    },
                ]
            }
        }
    )

    workloads: list[WorkloadInput] = Field(min_length=1)


class BatchItemResult(BaseModel):
    index: int
    status: str  # "success" | "failed"
    estimate: EstimateResponse | None = None
    error: ErrorDetail | None = None


class AggregateImpact(BaseModel):
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class BatchEstimateResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "batch_01hxyzabc123",
                "total_workloads": 2,
                "successful_estimates": 2,
                "failed_estimates": 0,
                "aggregate_impact": {
                    "energy": {
                        "status": "ok",
                        "min": 0.52,
                        "max": 0.71,
                        "unit": "Wh",
                        "total_workloads": 2,
                        "measured_workloads": 2,
                    },
                    "water": {
                        "status": "ok",
                        "min": 0.48,
                        "max": 0.60,
                        "unit": "mL",
                        "total_workloads": 2,
                        "measured_workloads": 2,
                    },
                    "carbon": {
                        "status": "ok",
                        "min": 0.07,
                        "max": 0.10,
                        "unit": "gCO2e",
                        "total_workloads": 2,
                        "measured_workloads": 2,
                    },
                },
                "results": [
                    {
                        "index": 0,
                        "status": "success",
                        "estimate": {
                            "estimate_id": "est_01hxyzabc123",
                            "energy": {"status": "ok", "min": 0.31, "max": 0.42, "unit": "Wh"},
                            "water": {"status": "ok", "min": 0.28, "max": 0.35, "unit": "mL"},
                            "carbon": {"status": "ok", "min": 0.04, "max": 0.06, "unit": "gCO2e"},
                            "confidence": "medium",
                            "evidence_level": 3,
                            "accounting_boundary": "B",
                            "methodology_version": "0.1",
                            "assumptions": ["Location-based grid emissions factor."],
                            "created_at": "2026-01-01T00:00:00Z",
                        },
                        "error": None,
                    },
                    {
                        "index": 1,
                        "status": "success",
                        "estimate": {
                            "estimate_id": "est_01hxyzabc456",
                            "energy": {"status": "ok", "min": 0.21, "max": 0.29, "unit": "Wh"},
                            "water": {"status": "ok", "min": 0.20, "max": 0.25, "unit": "mL"},
                            "carbon": {"status": "ok", "min": 0.03, "max": 0.04, "unit": "gCO2e"},
                            "confidence": "medium",
                            "evidence_level": 3,
                            "accounting_boundary": "B",
                            "methodology_version": "0.1",
                            "assumptions": ["Location-based grid emissions factor."],
                            "created_at": "2026-01-01T00:00:00Z",
                        },
                        "error": None,
                    },
                ],
            }
        }
    )

    batch_id: str
    total_workloads: int
    successful_estimates: int
    failed_estimates: int
    aggregate_impact: AggregateImpact
    results: list[BatchItemResult]
