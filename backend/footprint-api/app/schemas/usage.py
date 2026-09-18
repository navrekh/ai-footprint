from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AggregateMetricRange


class UsagePeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: datetime = Field(alias="from")
    to: datetime


class WorkloadCounts(BaseModel):
    """Measurement coverage is explicit and never implied: total is every
    workload matching the query; measured/partial/insufficient_data
    always sum back to total, and coverage_percent is measured/total -
    never silently rounded up to imply full coverage.
    """

    total: int
    measured: int
    partial: int
    insufficient_data: int
    coverage_percent: float


class UsageSummaryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z"},
                "workloads": {
                    "total": 10000,
                    "measured": 7000,
                    "partial": 2500,
                    "insufficient_data": 500,
                    "coverage_percent": 70.0,
                },
                "energy": {
                    "status": "partial",
                    "min": 428.3,
                    "max": 512.7,
                    "unit": "Wh",
                    "total_workloads": 10000,
                    "measured_workloads": 7000,
                },
                "water": {
                    "status": "partial",
                    "min": 390.1,
                    "max": 455.9,
                    "unit": "mL",
                    "total_workloads": 10000,
                    "measured_workloads": 7000,
                },
                "carbon": {
                    "status": "partial",
                    "min": 61.2,
                    "max": 73.8,
                    "unit": "gCO2e",
                    "total_workloads": 10000,
                    "measured_workloads": 7000,
                },
            }
        }
    )

    period: UsagePeriod
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByProviderItem(BaseModel):
    provider: str
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByProviderResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z"},
                "items": [
                    {
                        "provider": "openai",
                        "workloads": {
                            "total": 6000,
                            "measured": 6000,
                            "partial": 0,
                            "insufficient_data": 0,
                            "coverage_percent": 100.0,
                        },
                        "energy": {
                            "status": "ok",
                            "min": 250.0,
                            "max": 300.0,
                            "unit": "Wh",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                        "water": {
                            "status": "ok",
                            "min": 230.0,
                            "max": 265.0,
                            "unit": "mL",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                        "carbon": {
                            "status": "ok",
                            "min": 35.0,
                            "max": 42.0,
                            "unit": "gCO2e",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                    }
                ],
                "total": 1,
            }
        }
    )

    period: UsagePeriod
    items: list[UsageByProviderItem]
    total: int


class UsageByModelItem(BaseModel):
    provider: str
    model: str
    model_version: str | None
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByModelResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z"},
                "items": [
                    {
                        "provider": "openai",
                        "model": "model-id",
                        "model_version": "2026-01-01",
                        "workloads": {
                            "total": 6000,
                            "measured": 6000,
                            "partial": 0,
                            "insufficient_data": 0,
                            "coverage_percent": 100.0,
                        },
                        "energy": {
                            "status": "ok",
                            "min": 250.0,
                            "max": 300.0,
                            "unit": "Wh",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                        "water": {
                            "status": "ok",
                            "min": 230.0,
                            "max": 265.0,
                            "unit": "mL",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                        "carbon": {
                            "status": "ok",
                            "min": 35.0,
                            "max": 42.0,
                            "unit": "gCO2e",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                    }
                ],
                "total": 1,
            }
        }
    )

    period: UsagePeriod
    items: list[UsageByModelItem]
    total: int


class UsageByActivityItem(BaseModel):
    activity_type: str
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByActivityResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z"},
                "items": [
                    {
                        "activity_type": "text_generation",
                        "workloads": {
                            "total": 6000,
                            "measured": 6000,
                            "partial": 0,
                            "insufficient_data": 0,
                            "coverage_percent": 100.0,
                        },
                        "energy": {
                            "status": "ok",
                            "min": 250.0,
                            "max": 300.0,
                            "unit": "Wh",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                        "water": {
                            "status": "ok",
                            "min": 230.0,
                            "max": 265.0,
                            "unit": "mL",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                        "carbon": {
                            "status": "ok",
                            "min": 35.0,
                            "max": 42.0,
                            "unit": "gCO2e",
                            "total_workloads": 6000,
                            "measured_workloads": 6000,
                        },
                    }
                ],
                "total": 1,
            }
        }
    )

    period: UsagePeriod
    items: list[UsageByActivityItem]
    total: int


class UsageByApplicationItem(BaseModel):
    application_id: str
    application_name: str
    project_id: str
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByApplicationResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z"},
                "items": [
                    {
                        "application_id": "app_01hxyzabc123",
                        "application_name": "Customer Support Bot",
                        "project_id": "proj_01hxyzabc123",
                        "workloads": {
                            "total": 4000,
                            "measured": 4000,
                            "partial": 0,
                            "insufficient_data": 0,
                            "coverage_percent": 100.0,
                        },
                        "energy": {
                            "status": "ok",
                            "min": 150.0,
                            "max": 180.0,
                            "unit": "Wh",
                            "total_workloads": 4000,
                            "measured_workloads": 4000,
                        },
                        "water": {
                            "status": "ok",
                            "min": 140.0,
                            "max": 160.0,
                            "unit": "mL",
                            "total_workloads": 4000,
                            "measured_workloads": 4000,
                        },
                        "carbon": {
                            "status": "ok",
                            "min": 20.0,
                            "max": 25.0,
                            "unit": "gCO2e",
                            "total_workloads": 4000,
                            "measured_workloads": 4000,
                        },
                    }
                ],
                "total": 1,
            }
        }
    )

    period: UsagePeriod
    items: list[UsageByApplicationItem]
    total: int


class UsageTimeseriesPoint(BaseModel):
    period_start: datetime
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageTimeseriesResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": {"from": "2026-01-01T00:00:00Z", "to": "2026-01-03T00:00:00Z"},
                "granularity": "day",
                "items": [
                    {
                        "period_start": "2026-01-01T00:00:00Z",
                        "workloads": {
                            "total": 300,
                            "measured": 300,
                            "partial": 0,
                            "insufficient_data": 0,
                            "coverage_percent": 100.0,
                        },
                        "energy": {
                            "status": "ok",
                            "min": 12.5,
                            "max": 15.0,
                            "unit": "Wh",
                            "total_workloads": 300,
                            "measured_workloads": 300,
                        },
                        "water": {
                            "status": "ok",
                            "min": 11.5,
                            "max": 13.2,
                            "unit": "mL",
                            "total_workloads": 300,
                            "measured_workloads": 300,
                        },
                        "carbon": {
                            "status": "ok",
                            "min": 1.7,
                            "max": 2.1,
                            "unit": "gCO2e",
                            "total_workloads": 300,
                            "measured_workloads": 300,
                        },
                    },
                    {
                        "period_start": "2026-01-02T00:00:00Z",
                        "workloads": {
                            "total": 280,
                            "measured": 280,
                            "partial": 0,
                            "insufficient_data": 0,
                            "coverage_percent": 100.0,
                        },
                        "energy": {
                            "status": "ok",
                            "min": 11.6,
                            "max": 14.0,
                            "unit": "Wh",
                            "total_workloads": 280,
                            "measured_workloads": 280,
                        },
                        "water": {
                            "status": "ok",
                            "min": 10.7,
                            "max": 12.3,
                            "unit": "mL",
                            "total_workloads": 280,
                            "measured_workloads": 280,
                        },
                        "carbon": {
                            "status": "ok",
                            "min": 1.6,
                            "max": 1.9,
                            "unit": "gCO2e",
                            "total_workloads": 280,
                            "measured_workloads": 280,
                        },
                    },
                ],
            }
        }
    )

    period: UsagePeriod
    granularity: str
    items: list[UsageTimeseriesPoint]
