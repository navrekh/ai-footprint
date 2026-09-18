"""`aifootprint usage <subcommand>` - the six existing GET /v1/usage/*
endpoints, through `AIClient.usage.*` only (Sprint 7 FRD section 39.6).
Every filter maps 1:1 to an existing backend query parameter - none are
invented here.
"""

from __future__ import annotations

import argparse
from datetime import datetime

from aifootprint import AIClient
from aifootprint.models import (
    ResultBase,
    UsageByActivityResult,
    UsageByApplicationResult,
    UsageByModelResult,
    UsageByProviderResult,
    UsageSummary,
    UsageTimeseriesResult,
)

from ..output import format_range, format_workload_counts, print_json, print_request_id
from ._shared import ACTIVITY_TYPES, add_global_options


def _add_common_filters(parser: argparse.ArgumentParser, *, application: bool) -> None:
    parser.add_argument("--from", dest="from_", default=None, help="ISO 8601 start (inclusive).")
    parser.add_argument("--to", dest="to", default=None, help="ISO 8601 end (exclusive).")
    parser.add_argument("--project", dest="project_id", default=None)
    if application:
        parser.add_argument("--application", dest="application_id", default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--activity-type", default=None, choices=ACTIVITY_TYPES)


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def register(subparsers: argparse._SubParsersAction) -> None:
    usage_parser = subparsers.add_parser("usage", help="Usage and resource-impact intelligence")
    usage_subparsers = usage_parser.add_subparsers(dest="usage_command", required=True)

    summary = usage_subparsers.add_parser("summary", help="Aggregate usage over a period")
    _add_common_filters(summary, application=True)
    add_global_options(summary)
    summary.set_defaults(handler=run_summary, renderer=render)

    by_provider = usage_subparsers.add_parser("by-provider", help="Usage grouped by provider")
    _add_common_filters(by_provider, application=True)
    by_provider.add_argument("--limit", type=int, default=50)
    by_provider.add_argument("--offset", type=int, default=0)
    add_global_options(by_provider)
    by_provider.set_defaults(handler=run_by_provider, renderer=render)

    by_model = usage_subparsers.add_parser("by-model", help="Usage grouped by model")
    _add_common_filters(by_model, application=True)
    by_model.add_argument("--limit", type=int, default=50)
    by_model.add_argument("--offset", type=int, default=0)
    add_global_options(by_model)
    by_model.set_defaults(handler=run_by_model, renderer=render)

    by_activity = usage_subparsers.add_parser("by-activity", help="Usage grouped by activity type")
    _add_common_filters(by_activity, application=True)
    by_activity.add_argument("--limit", type=int, default=50)
    by_activity.add_argument("--offset", type=int, default=0)
    add_global_options(by_activity)
    by_activity.set_defaults(handler=run_by_activity, renderer=render)

    by_application = usage_subparsers.add_parser(
        "by-application",
        help="Usage grouped by application (does not accept --application - it IS the grouping)",
    )
    _add_common_filters(by_application, application=False)
    by_application.add_argument("--limit", type=int, default=50)
    by_application.add_argument("--offset", type=int, default=0)
    add_global_options(by_application)
    by_application.set_defaults(handler=run_by_application, renderer=render)

    timeseries = usage_subparsers.add_parser("timeseries", help="Usage over time")
    _add_common_filters(timeseries, application=True)
    timeseries.add_argument("--granularity", choices=["day", "week", "month"], default="day")
    add_global_options(timeseries)
    timeseries.set_defaults(handler=run_timeseries, renderer=render)


def run_summary(args: argparse.Namespace, client: AIClient) -> UsageSummary:
    return client.usage.summary(
        from_=_parse_datetime(args.from_),
        to=_parse_datetime(args.to),
        project_id=args.project_id,
        application_id=args.application_id,
        provider=args.provider,
        model=args.model,
        activity_type=args.activity_type,
    )


def run_by_provider(args: argparse.Namespace, client: AIClient) -> UsageByProviderResult:
    return client.usage.by_provider(
        from_=_parse_datetime(args.from_),
        to=_parse_datetime(args.to),
        project_id=args.project_id,
        application_id=args.application_id,
        provider=args.provider,
        model=args.model,
        activity_type=args.activity_type,
        limit=args.limit,
        offset=args.offset,
    )


def run_by_model(args: argparse.Namespace, client: AIClient) -> UsageByModelResult:
    return client.usage.by_model(
        from_=_parse_datetime(args.from_),
        to=_parse_datetime(args.to),
        project_id=args.project_id,
        application_id=args.application_id,
        provider=args.provider,
        model=args.model,
        activity_type=args.activity_type,
        limit=args.limit,
        offset=args.offset,
    )


def run_by_activity(args: argparse.Namespace, client: AIClient) -> UsageByActivityResult:
    return client.usage.by_activity(
        from_=_parse_datetime(args.from_),
        to=_parse_datetime(args.to),
        project_id=args.project_id,
        application_id=args.application_id,
        provider=args.provider,
        model=args.model,
        activity_type=args.activity_type,
        limit=args.limit,
        offset=args.offset,
    )


def run_by_application(args: argparse.Namespace, client: AIClient) -> UsageByApplicationResult:
    return client.usage.by_application(
        from_=_parse_datetime(args.from_),
        to=_parse_datetime(args.to),
        project_id=args.project_id,
        provider=args.provider,
        model=args.model,
        activity_type=args.activity_type,
        limit=args.limit,
        offset=args.offset,
    )


def run_timeseries(args: argparse.Namespace, client: AIClient) -> UsageTimeseriesResult:
    return client.usage.timeseries(
        granularity=args.granularity,
        from_=_parse_datetime(args.from_),
        to=_parse_datetime(args.to),
        project_id=args.project_id,
        application_id=args.application_id,
        provider=args.provider,
        model=args.model,
        activity_type=args.activity_type,
    )


def render(result: ResultBase, output: str) -> None:
    if output == "json":
        print_json(result)
        return
    if isinstance(result, UsageSummary):
        _render_summary(result)
    elif isinstance(result, UsageByProviderResult):
        _render_items(result.items, lambda item: item.provider, result)
    elif isinstance(result, UsageByModelResult):
        _render_items(
            result.items,
            lambda item: (
                f"{item.provider}/{item.model}"
                + (f"@{item.model_version}" if item.model_version else "")
            ),
            result,
        )
    elif isinstance(result, UsageByActivityResult):
        _render_items(result.items, lambda item: item.activity_type, result)
    elif isinstance(result, UsageByApplicationResult):
        _render_items(result.items, lambda item: item.application_name, result)
    elif isinstance(result, UsageTimeseriesResult):
        _render_timeseries(result)
    print_request_id(result)


def _render_summary(result: UsageSummary) -> None:
    print(f"Period: {result.period.from_.isoformat()} - {result.period.to.isoformat()}")
    print(format_workload_counts(result.workloads))
    print(f"Energy: {format_range(result.energy)}")
    print(f"Water: {format_range(result.water)}")
    print(f"Carbon: {format_range(result.carbon)}")


def _render_items(items, label_fn, result) -> None:
    print(f"Period: {result.period.from_.isoformat()} - {result.period.to.isoformat()}")
    if not items:
        print("(no items)")
        return
    for item in items:
        print(f"- {label_fn(item)}")
        print(f"    {format_workload_counts(item.workloads)}")
        print(
            f"    Energy: {format_range(item.energy)} | "
            f"Water: {format_range(item.water)} | "
            f"Carbon: {format_range(item.carbon)}"
        )


def _render_timeseries(result: UsageTimeseriesResult) -> None:
    print(f"Period: {result.period.from_.isoformat()} - {result.period.to.isoformat()}")
    print(f"Granularity: {result.granularity}")
    if not result.items:
        print("(no items)")
        return
    for point in result.items:
        print(f"- {point.period_start.isoformat()}")
        print(f"    {format_workload_counts(point.workloads)}")
        print(
            f"    Energy: {format_range(point.energy)} | "
            f"Water: {format_range(point.water)} | "
            f"Carbon: {format_range(point.carbon)}"
        )
