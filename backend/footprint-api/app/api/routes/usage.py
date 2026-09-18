from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.errors import ErrorCode
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.models.enums import ActivityType, UsageGranularity
from app.schemas.usage import (
    UsageByActivityResponse,
    UsageByApplicationResponse,
    UsageByModelResponse,
    UsageByProviderResponse,
    UsageSummaryResponse,
    UsageTimeseriesResponse,
)
from app.services.application_service import ApplicationService
from app.services.auth_service import AuthContext
from app.services.tenant_context import resolve_optional_project_filter
from app.services.usage_service import UsageFilters, UsageService, resolve_period

router = APIRouter(prefix="/usage")

# Shared by every usage endpoint: the same auth dependency, the same
# resolve_period()/ApplicationService.get_owned() calls inside
# _build_filters() below, so the same set of possible errors.
_USAGE_ERRORS = error_responses(*AUTH_ERRORS, ErrorCode.INVALID_DATE_RANGE, ErrorCode.NOT_FOUND)


async def _build_filters(
    db: AsyncSession,
    auth: AuthContext,
    *,
    from_ts: datetime | None,
    to_ts: datetime | None,
    project: str | None,
    application: str | None,
    provider: str | None,
    model: str | None,
    activity_type: ActivityType | None,
) -> UsageFilters:
    resolved_from, resolved_to = resolve_period(from_ts, to_ts)
    project_filter = resolve_optional_project_filter(auth, project)

    if application is not None:
        # Validates the application belongs to the authorized
        # organization/project scope - raises NotFoundError otherwise,
        # never revealing whether it exists elsewhere (FRD section 18).
        await ApplicationService(db).get_owned(
            auth.organization.id, application, project_id=project_filter
        )

    return UsageFilters(
        organization_id=auth.organization.id,
        from_ts=resolved_from,
        to_ts=resolved_to,
        project_id=project_filter,
        application_id=application,
        provider=provider,
        model=model,
        activity_type=activity_type.value if activity_type else None,
    )


@router.get(
    "/summary",
    response_model=UsageSummaryResponse,
    tags=["usage"],
    summary="Aggregate workload counts, coverage and resource ranges for a period",
    description=(
        "Reports total/measured/partial/insufficient_data workload counts, measurement "
        "coverage, and additive min/max energy/water/carbon ranges - never a false point "
        "estimate. Derived from persisted workloads/estimates; no separate usage ledger."
    ),
    responses=_USAGE_ERRORS,
)
async def get_usage_summary(
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive start of the period (ISO 8601). Defaults to 30 days before `to`.",
    ),
    to: datetime | None = Query(
        default=None, description="Exclusive end of the period (ISO 8601). Defaults to now."
    ),
    project: str | None = Query(
        default=None,
        description=(
            "Filter by project id. A project-scoped key is hard-limited to its own "
            "project regardless of this filter."
        ),
    ),
    application: str | None = Query(
        default=None, description="Filter by application id. Must belong to the authorized project."
    ),
    provider: str | None = Query(default=None, description="Filter by provider id."),
    model: str | None = Query(default=None, description="Filter by model name."),
    activity_type: ActivityType | None = Query(
        default=None, description="Filter by activity type."
    ),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UsageSummaryResponse:
    filters = await _build_filters(
        db,
        auth,
        from_ts=from_,
        to_ts=to,
        project=project,
        application=application,
        provider=provider,
        model=model,
        activity_type=activity_type,
    )
    return await UsageService(db).get_summary(filters)


@router.get(
    "/by-provider",
    response_model=UsageByProviderResponse,
    tags=["usage"],
    summary="Usage grouped by provider",
    description="Same semantics as /usage/summary, grouped by provider. Limit/offset paginated.",
    responses=_USAGE_ERRORS,
)
async def get_usage_by_provider(
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive start of the period (ISO 8601). Defaults to 30 days before `to`.",
    ),
    to: datetime | None = Query(
        default=None, description="Exclusive end of the period (ISO 8601). Defaults to now."
    ),
    project: str | None = Query(
        default=None,
        description=(
            "Filter by project id. A project-scoped key is hard-limited to its own "
            "project regardless of this filter."
        ),
    ),
    application: str | None = Query(
        default=None, description="Filter by application id. Must belong to the authorized project."
    ),
    provider: str | None = Query(default=None, description="Filter by provider id."),
    model: str | None = Query(default=None, description="Filter by model name."),
    activity_type: ActivityType | None = Query(
        default=None, description="Filter by activity type."
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Page size (1-200)."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UsageByProviderResponse:
    filters = await _build_filters(
        db,
        auth,
        from_ts=from_,
        to_ts=to,
        project=project,
        application=application,
        provider=provider,
        model=model,
        activity_type=activity_type,
    )
    return await UsageService(db).get_by_provider(filters, limit=limit, offset=offset)


@router.get(
    "/by-model",
    response_model=UsageByModelResponse,
    tags=["usage"],
    summary="Usage grouped by provider/model/model_version",
    description=(
        "Same semantics as /usage/summary, grouped by provider/model/version. "
        "Limit/offset paginated."
    ),
    responses=_USAGE_ERRORS,
)
async def get_usage_by_model(
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive start of the period (ISO 8601). Defaults to 30 days before `to`.",
    ),
    to: datetime | None = Query(
        default=None, description="Exclusive end of the period (ISO 8601). Defaults to now."
    ),
    project: str | None = Query(
        default=None,
        description=(
            "Filter by project id. A project-scoped key is hard-limited to its own "
            "project regardless of this filter."
        ),
    ),
    application: str | None = Query(
        default=None, description="Filter by application id. Must belong to the authorized project."
    ),
    provider: str | None = Query(default=None, description="Filter by provider id."),
    model: str | None = Query(default=None, description="Filter by model name."),
    activity_type: ActivityType | None = Query(
        default=None, description="Filter by activity type."
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Page size (1-200)."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UsageByModelResponse:
    filters = await _build_filters(
        db,
        auth,
        from_ts=from_,
        to_ts=to,
        project=project,
        application=application,
        provider=provider,
        model=model,
        activity_type=activity_type,
    )
    return await UsageService(db).get_by_model(filters, limit=limit, offset=offset)


@router.get(
    "/by-activity",
    response_model=UsageByActivityResponse,
    tags=["usage"],
    summary="Usage grouped by activity type",
    description=(
        "Same semantics as /usage/summary, grouped by activity type. Limit/offset paginated."
    ),
    responses=_USAGE_ERRORS,
)
async def get_usage_by_activity(
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive start of the period (ISO 8601). Defaults to 30 days before `to`.",
    ),
    to: datetime | None = Query(
        default=None, description="Exclusive end of the period (ISO 8601). Defaults to now."
    ),
    project: str | None = Query(
        default=None,
        description=(
            "Filter by project id. A project-scoped key is hard-limited to its own "
            "project regardless of this filter."
        ),
    ),
    application: str | None = Query(
        default=None, description="Filter by application id. Must belong to the authorized project."
    ),
    provider: str | None = Query(default=None, description="Filter by provider id."),
    model: str | None = Query(default=None, description="Filter by model name."),
    activity_type: ActivityType | None = Query(
        default=None, description="Filter by activity type."
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Page size (1-200)."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UsageByActivityResponse:
    filters = await _build_filters(
        db,
        auth,
        from_ts=from_,
        to_ts=to,
        project=project,
        application=application,
        provider=provider,
        model=model,
        activity_type=activity_type,
    )
    return await UsageService(db).get_by_activity(filters, limit=limit, offset=offset)


@router.get(
    "/by-application",
    response_model=UsageByApplicationResponse,
    tags=["usage"],
    summary="Usage grouped by application",
    description=(
        "Same semantics as /usage/summary, grouped by application. Excludes workloads with "
        "no application (rather than a synthetic 'unassigned' bucket). Limit/offset paginated. "
        "Does not accept an `application` filter - use /usage/summary for that."
    ),
    responses=_USAGE_ERRORS,
)
async def get_usage_by_application(
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive start of the period (ISO 8601). Defaults to 30 days before `to`.",
    ),
    to: datetime | None = Query(
        default=None, description="Exclusive end of the period (ISO 8601). Defaults to now."
    ),
    project: str | None = Query(
        default=None,
        description=(
            "Filter by project id. A project-scoped key is hard-limited to its own "
            "project regardless of this filter."
        ),
    ),
    provider: str | None = Query(default=None, description="Filter by provider id."),
    model: str | None = Query(default=None, description="Filter by model name."),
    activity_type: ActivityType | None = Query(
        default=None, description="Filter by activity type."
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Page size (1-200)."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UsageByApplicationResponse:
    filters = await _build_filters(
        db,
        auth,
        from_ts=from_,
        to_ts=to,
        project=project,
        application=None,
        provider=provider,
        model=model,
        activity_type=activity_type,
    )
    return await UsageService(db).get_by_application(filters, limit=limit, offset=offset)


@router.get(
    "/timeseries",
    response_model=UsageTimeseriesResponse,
    tags=["usage"],
    summary="Usage aggregated into day/week/month time buckets",
    description=(
        "Bounded to a maximum of 400 buckets rather than paginated - narrow the date range "
        "or use a coarser granularity if the request is rejected with INVALID_DATE_RANGE."
    ),
    responses=_USAGE_ERRORS,
)
async def get_usage_timeseries(
    granularity: UsageGranularity = Query(
        default=UsageGranularity.DAY, description="Time-bucket size: day, week, or month."
    ),
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive start of the period (ISO 8601). Defaults to 30 days before `to`.",
    ),
    to: datetime | None = Query(
        default=None, description="Exclusive end of the period (ISO 8601). Defaults to now."
    ),
    project: str | None = Query(
        default=None,
        description=(
            "Filter by project id. A project-scoped key is hard-limited to its own "
            "project regardless of this filter."
        ),
    ),
    application: str | None = Query(
        default=None, description="Filter by application id. Must belong to the authorized project."
    ),
    provider: str | None = Query(default=None, description="Filter by provider id."),
    model: str | None = Query(default=None, description="Filter by model name."),
    activity_type: ActivityType | None = Query(
        default=None, description="Filter by activity type."
    ),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UsageTimeseriesResponse:
    filters = await _build_filters(
        db,
        auth,
        from_ts=from_,
        to_ts=to,
        project=project,
        application=application,
        provider=provider,
        model=model,
        activity_type=activity_type,
    )
    return await UsageService(db).get_timeseries(filters, granularity=granularity)
