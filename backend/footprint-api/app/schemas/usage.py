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
    period: UsagePeriod
    granularity: str
    items: list[UsageTimeseriesPoint]
