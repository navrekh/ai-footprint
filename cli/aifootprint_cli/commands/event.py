"""`aifootprint event` - submits a persisted AIWorkload via the existing
`POST /v1/events` endpoint, through `AIClient.events.create()` only
(Sprint 7 FRD section 39.4). No HTTP call is made from this module.
"""

from __future__ import annotations

import argparse

from aifootprint import AIClient
from aifootprint.models import Event

from ..context import build_client_context
from ..output import format_request_id, print_json, print_kv
from ._shared import (
    ACTIVITY_TYPES,
    MODALITIES,
    add_global_options,
    add_workload_quantity_options,
    parse_metadata,
    workload_quantity_kwargs,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "event",
        help="Submit a persisted AI workload event (POST /v1/events)",
        description=(
            "Persists an AIWorkload and its Estimate. Requires an API key. Never send "
            "prompt or response content in --metadata."
        ),
    )
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--modality", required=True, choices=MODALITIES)
    parser.add_argument("--activity-type", required=True, choices=ACTIVITY_TYPES)
    add_workload_quantity_options(parser)
    parser.add_argument("--project", dest="project_id", default=None, help="Target project id.")
    parser.add_argument(
        "--application", dest="application_id", default=None, help="Target application id."
    )
    parser.add_argument(
        "--metadata", default=None, help='Arbitrary JSON object, e.g. \'{"env": "ci"}\'.'
    )
    parser.add_argument(
        "--idempotency-key",
        default=None,
        help="Resubmitting the same key for the same project replays the original result.",
    )
    add_global_options(parser)
    parser.set_defaults(handler=run, renderer=render)


def run(args: argparse.Namespace, client: AIClient) -> Event:
    result = client.events.create(
        provider=args.provider,
        model=args.model,
        model_version=args.model_version,
        modality=args.modality,
        activity_type=args.activity_type,
        **workload_quantity_kwargs(args),
        project_id=args.project_id,
        application_id=args.application_id,
        metadata=parse_metadata(args.metadata),
        idempotency_key=args.idempotency_key,
        client=build_client_context(),
    )
    return result


def render(result: Event, output: str) -> None:
    if output == "json":
        print_json(result)
        return
    print_kv("Workload ID", result.workload_id)
    print_kv("Estimate ID", result.estimate_id)
    print_kv("Status", result.status)
    print_kv("Idempotent replay", "yes" if result.idempotent_replay else "no")
    request_id_line = format_request_id(result)
    if request_id_line:
        print(request_id_line)
