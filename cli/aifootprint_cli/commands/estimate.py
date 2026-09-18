"""`aifootprint estimate` - stateless estimation via the existing
`POST /v1/estimate` endpoint, through `AIClient.estimates.create()`
only (Sprint 7 FRD section 39.5). Zero local estimation logic: every
field printed below comes directly from the API response.
"""

from __future__ import annotations

import argparse

from aifootprint import AIClient
from aifootprint.models import Estimate

from ..output import format_enum, format_range, format_request_id, print_json, print_kv
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
        "estimate",
        help="Calculate a stateless workload estimate (POST /v1/estimate)",
        description="Nothing is persisted. Requires an API key but touches no tenant-owned data.",
    )
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--modality", required=True, choices=MODALITIES)
    parser.add_argument("--activity-type", required=True, choices=ACTIVITY_TYPES)
    add_workload_quantity_options(parser)
    parser.add_argument("--metadata", default=None, help="Arbitrary JSON object.")
    add_global_options(parser)
    parser.set_defaults(handler=run, renderer=render)


def run(args: argparse.Namespace, client: AIClient) -> Estimate:
    return client.estimates.create(
        provider=args.provider,
        model=args.model,
        model_version=args.model_version,
        modality=args.modality,
        activity_type=args.activity_type,
        **workload_quantity_kwargs(args),
        metadata=parse_metadata(args.metadata),
    )


def render(result: Estimate, output: str) -> None:
    if output == "json":
        print_json(result)
        return
    print_kv("Energy", format_range(result.energy))
    print_kv("Water", format_range(result.water))
    print_kv("Carbon", format_range(result.carbon))
    confidence = format_enum(result.confidence) if result.confidence else "Insufficient data"
    print_kv("Confidence", confidence)
    print_kv(
        "Evidence level", str(result.evidence_level) if result.evidence_level is not None else "-"
    )
    print_kv("Accounting boundary", result.accounting_boundary or "-")
    print_kv("Methodology version", result.methodology_version or "-")
    if result.assumptions:
        print("Assumptions:")
        for assumption in result.assumptions:
            print(f"  - {assumption}")
    request_id_line = format_request_id(result)
    if request_id_line:
        print(request_id_line)
