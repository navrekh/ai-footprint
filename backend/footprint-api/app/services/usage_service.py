from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidDateRangeError
from app.db.base import utcnow
from app.methodology.uncertainty import determine_metric_status
from app.models.application import Application
from app.models.enums import MetricStatus, UsageGranularity
from app.models.estimate import Estimate
from app.models.workload import AIWorkload
from app.schemas.common import AggregateMetricRange
from app.schemas.usage import (
    UsageByActivityItem,
    UsageByActivityResponse,
    UsageByApplicationItem,
    UsageByApplicationResponse,
    UsageByModelItem,
    UsageByModelResponse,
    UsageByProviderItem,
    UsageByProviderResponse,
    UsagePeriod,
    UsageSummaryResponse,
    UsageTimeseriesPoint,
    UsageTimeseriesResponse,
    WorkloadCounts,
)

DEFAULT_LOOKBACK_DAYS = 30
MAX_TIMESERIES_BUCKETS = 400
_APPROX_DAYS_PER_BUCKET: dict[UsageGranularity, int] = {
    UsageGranularity.DAY: 1,
    UsageGranularity.WEEK: 7,
    UsageGranularity.MONTH: 30,
}
_UNITS = {"energy": "Wh", "water": "mL", "carbon": "gCO2e"}

# --- Shared aggregate column expressions -----------------------------------
# Built once and reused across every usage query (summary, breakdowns,
# time series) - the same additive, per-metric-independent aggregation
# math as UncertaintyEngine.aggregate() and BatchService, just pushed down
# to PostgreSQL instead of run over an in-memory list (sprint 3:
# "prefer database-side aggregation... avoid loading entire workload
# datasets into Python").

_energy_ok = Estimate.energy_status == MetricStatus.OK.value
_water_ok = Estimate.water_status == MetricStatus.OK.value
_carbon_ok = Estimate.carbon_status == MetricStatus.OK.value
_all_ok = and_(_energy_ok, _water_ok, _carbon_ok)
_any_ok = or_(_energy_ok, _water_ok, _carbon_ok)

_total_col = func.count().label("total")
_measured_col = func.count().filter(_all_ok).label("measured")
_partial_col = func.count().filter(and_(_any_ok, not_(_all_ok))).label("partial")
_insufficient_col = func.count().filter(not_(_any_ok)).label("insufficient_data")

_energy_min_col = func.sum(Estimate.energy_min_wh).filter(_energy_ok).label("energy_min")
_energy_max_col = func.sum(Estimate.energy_max_wh).filter(_energy_ok).label("energy_max")
_energy_measured_col = func.count().filter(_energy_ok).label("energy_measured")

_water_min_col = func.sum(Estimate.water_min_ml).filter(_water_ok).label("water_min")
_water_max_col = func.sum(Estimate.water_max_ml).filter(_water_ok).label("water_max")
_water_measured_col = func.count().filter(_water_ok).label("water_measured")

_carbon_min_col = func.sum(Estimate.carbon_min_g).filter(_carbon_ok).label("carbon_min")
_carbon_max_col = func.sum(Estimate.carbon_max_g).filter(_carbon_ok).label("carbon_max")
_carbon_measured_col = func.count().filter(_carbon_ok).label("carbon_measured")

_AGGREGATE_COLUMNS: list[Any] = [
    _total_col,
    _measured_col,
    _partial_col,
    _insufficient_col,
    _energy_min_col,
    _energy_max_col,
    _energy_measured_col,
    _water_min_col,
    _water_max_col,
    _water_measured_col,
    _carbon_min_col,
    _carbon_max_col,
    _carbon_measured_col,
]


def resolve_period(from_ts: datetime | None, to_ts: datetime | None) -> tuple[datetime, datetime]:
    """Resolves the effective (from, to) window, defaulting to the last
    DEFAULT_LOOKBACK_DAYS when omitted - usage endpoints always report an
    explicit period, even when the caller does not supply one.
    """
    resolved_to = to_ts or utcnow()
    resolved_from = from_ts or (resolved_to - timedelta(days=DEFAULT_LOOKBACK_DAYS))
    if resolved_from > resolved_to:
        raise InvalidDateRangeError("'from' must not be after 'to'.")
    return resolved_from, resolved_to


@dataclass
class UsageFilters:
    organization_id: str
    from_ts: datetime
    to_ts: datetime
    project_id: str | None = None
    application_id: str | None = None
    provider: str | None = None
    model: str | None = None
    activity_type: str | None = None


def _workload_counts_from_row(row) -> WorkloadCounts:
    total = row.total
    measured = row.measured
    coverage = round((measured / total * 100.0), 2) if total > 0 else 0.0
    return WorkloadCounts(
        total=total,
        measured=measured,
        partial=row.partial,
        insufficient_data=row.insufficient_data,
        coverage_percent=coverage,
    )


def _metric_range_from_row(row, prefix: str) -> AggregateMetricRange:
    total = row.total
    measured = getattr(row, f"{prefix}_measured")
    status = determine_metric_status(total, measured)
    return AggregateMetricRange(
        status=status,
        min=getattr(row, f"{prefix}_min"),
        max=getattr(row, f"{prefix}_max"),
        unit=_UNITS[prefix],
        total_workloads=total,
        measured_workloads=measured,
    )


class UsageService:
    """Derives usage intelligence entirely from persisted AIWorkload and
    Estimate rows via PostgreSQL aggregation - no separate usage ledger
    or materialized table (FRD section 17).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_filters(self, stmt, filters: UsageFilters):
        stmt = (
            stmt.where(AIWorkload.organization_id == filters.organization_id)
            .where(AIWorkload.timestamp >= filters.from_ts)
            .where(AIWorkload.timestamp <= filters.to_ts)
        )
        if filters.project_id is not None:
            stmt = stmt.where(AIWorkload.project_id == filters.project_id)
        if filters.application_id is not None:
            stmt = stmt.where(AIWorkload.application_id == filters.application_id)
        if filters.provider is not None:
            stmt = stmt.where(AIWorkload.provider == filters.provider)
        if filters.model is not None:
            stmt = stmt.where(AIWorkload.model == filters.model)
        if filters.activity_type is not None:
            stmt = stmt.where(AIWorkload.activity_type == filters.activity_type)
        return stmt

    def _base_query(self, filters: UsageFilters):
        stmt = (
            select(*_AGGREGATE_COLUMNS)
            .select_from(AIWorkload)
            .join(Estimate, Estimate.workload_id == AIWorkload.id)
        )
        return self._apply_filters(stmt, filters)

    async def get_summary(self, filters: UsageFilters) -> UsageSummaryResponse:
        row = (await self._db.execute(self._base_query(filters))).one()
        return UsageSummaryResponse(
            period=UsagePeriod(from_=filters.from_ts, to=filters.to_ts),
            workloads=_workload_counts_from_row(row),
            energy=_metric_range_from_row(row, "energy"),
            water=_metric_range_from_row(row, "water"),
            carbon=_metric_range_from_row(row, "carbon"),
        )

    async def _run_grouped(
        self,
        filters: UsageFilters,
        *,
        group_columns: list[Any],
        extra_select: list[Any],
        limit: int,
        offset: int,
    ):
        base = (
            select(*extra_select, *_AGGREGATE_COLUMNS)
            .select_from(AIWorkload)
            .join(Estimate, Estimate.workload_id == AIWorkload.id)
        )
        base = self._apply_filters(base, filters)
        grouped = base.group_by(*group_columns)

        total_groups = (
            await self._db.execute(select(func.count()).select_from(grouped.subquery()))
        ).scalar_one()

        paged_stmt = (
            grouped.order_by(_total_col.desc(), *group_columns).limit(limit).offset(offset)
        )
        rows = (await self._db.execute(paged_stmt)).all()
        return rows, total_groups

    async def get_by_provider(
        self, filters: UsageFilters, *, limit: int, offset: int
    ) -> UsageByProviderResponse:
        rows, total = await self._run_grouped(
            filters,
            group_columns=[AIWorkload.provider],
            extra_select=[AIWorkload.provider],
            limit=limit,
            offset=offset,
        )
        items = [
            UsageByProviderItem(
                provider=row.provider,
                workloads=_workload_counts_from_row(row),
                energy=_metric_range_from_row(row, "energy"),
                water=_metric_range_from_row(row, "water"),
                carbon=_metric_range_from_row(row, "carbon"),
            )
            for row in rows
        ]
        return UsageByProviderResponse(
            period=UsagePeriod(from_=filters.from_ts, to=filters.to_ts), items=items, total=total
        )

    async def get_by_model(
        self, filters: UsageFilters, *, limit: int, offset: int
    ) -> UsageByModelResponse:
        rows, total = await self._run_grouped(
            filters,
            group_columns=[AIWorkload.provider, AIWorkload.model, AIWorkload.model_version],
            extra_select=[AIWorkload.provider, AIWorkload.model, AIWorkload.model_version],
            limit=limit,
            offset=offset,
        )
        items = [
            UsageByModelItem(
                provider=row.provider,
                model=row.model,
                model_version=row.model_version,
                workloads=_workload_counts_from_row(row),
                energy=_metric_range_from_row(row, "energy"),
                water=_metric_range_from_row(row, "water"),
                carbon=_metric_range_from_row(row, "carbon"),
            )
            for row in rows
        ]
        return UsageByModelResponse(
            period=UsagePeriod(from_=filters.from_ts, to=filters.to_ts), items=items, total=total
        )

    async def get_by_activity(
        self, filters: UsageFilters, *, limit: int, offset: int
    ) -> UsageByActivityResponse:
        rows, total = await self._run_grouped(
            filters,
            group_columns=[AIWorkload.activity_type],
            extra_select=[AIWorkload.activity_type],
            limit=limit,
            offset=offset,
        )
        items = [
            UsageByActivityItem(
                activity_type=row.activity_type,
                workloads=_workload_counts_from_row(row),
                energy=_metric_range_from_row(row, "energy"),
                water=_metric_range_from_row(row, "water"),
                carbon=_metric_range_from_row(row, "carbon"),
            )
            for row in rows
        ]
        return UsageByActivityResponse(
            period=UsagePeriod(from_=filters.from_ts, to=filters.to_ts), items=items, total=total
        )

    async def get_by_application(
        self, filters: UsageFilters, *, limit: int, offset: int
    ) -> UsageByApplicationResponse:
        base = (
            select(
                Application.id.label("application_id"),
                Application.name.label("application_name"),
                Application.project_id,
                *_AGGREGATE_COLUMNS,
            )
            .select_from(AIWorkload)
            .join(Estimate, Estimate.workload_id == AIWorkload.id)
            .join(Application, Application.id == AIWorkload.application_id)
        )
        base = self._apply_filters(base, filters)
        # Only workloads actually associated with an application can
        # appear in this breakdown - unassigned workloads are excluded
        # rather than grouped under a synthetic "none" bucket.
        base = base.where(AIWorkload.application_id.isnot(None))
        grouped = base.group_by(Application.id, Application.name, Application.project_id)

        total_groups = (
            await self._db.execute(select(func.count()).select_from(grouped.subquery()))
        ).scalar_one()
        paged_stmt = grouped.order_by(_total_col.desc(), Application.id).limit(limit).offset(offset)
        rows = (await self._db.execute(paged_stmt)).all()

        items = [
            UsageByApplicationItem(
                application_id=row.application_id,
                application_name=row.application_name,
                project_id=row.project_id,
                workloads=_workload_counts_from_row(row),
                energy=_metric_range_from_row(row, "energy"),
                water=_metric_range_from_row(row, "water"),
                carbon=_metric_range_from_row(row, "carbon"),
            )
            for row in rows
        ]
        return UsageByApplicationResponse(
            period=UsagePeriod(from_=filters.from_ts, to=filters.to_ts),
            items=items,
            total=total_groups,
        )

    async def get_timeseries(
        self, filters: UsageFilters, *, granularity: UsageGranularity
    ) -> UsageTimeseriesResponse:
        span_days = (filters.to_ts - filters.from_ts).days + 1
        approx_buckets = max(1, span_days // _APPROX_DAYS_PER_BUCKET[granularity])
        if approx_buckets > MAX_TIMESERIES_BUCKETS:
            raise InvalidDateRangeError(
                f"Requested range produces too many buckets for granularity "
                f"'{granularity.value}' (limit {MAX_TIMESERIES_BUCKETS}). Use a narrower "
                "date range or a coarser granularity."
            )

        bucket_col = func.date_trunc(
            granularity.value, func.timezone("UTC", AIWorkload.timestamp)
        ).label("bucket")
        base = (
            select(bucket_col, *_AGGREGATE_COLUMNS)
            .select_from(AIWorkload)
            .join(Estimate, Estimate.workload_id == AIWorkload.id)
        )
        base = self._apply_filters(base, filters)
        grouped = base.group_by(bucket_col).order_by(bucket_col)

        rows = (await self._db.execute(grouped)).all()

        items = [
            UsageTimeseriesPoint(
                period_start=row.bucket,
                workloads=_workload_counts_from_row(row),
                energy=_metric_range_from_row(row, "energy"),
                water=_metric_range_from_row(row, "water"),
                carbon=_metric_range_from_row(row, "carbon"),
            )
            for row in rows
        ]
        return UsageTimeseriesResponse(
            period=UsagePeriod(from_=filters.from_ts, to=filters.to_ts),
            granularity=granularity.value,
            items=items,
        )
