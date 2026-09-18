"""`aifootprint compare` - independent per-candidate estimation via the
existing `POST /v1/compare`, through `AIClient.compare.create()` only
(Sprint 7 FRD section 39.7). Candidates are rendered in exactly the
order the API returned them - this module contains no sort/score/rank/
recommend logic of any kind, matching docs/ARCHITECTURE.md ADR-008.
"""

from __future__ import annotations

import argparse

from aifootprint import AIClient
from aifootprint.models import CompareResult

from ..output import print_json
from ._comparison import render_comparison_results
from ._shared import (
    ACTIVITY_TYPES,
    MODALITIES,
    add_global_options,
    add_workload_quantity_options,
    parse_candidates,
    parse_metadata,
    workload_quantity_kwargs,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "compare",
        help="Evaluate one workload independently across candidates (POST /v1/compare)",
        description=(
            "Each candidate is estimated independently. Results are shown in API-returned "
            "order - never ranked, scored, or labeled a winner."
        ),
    )
    parser.add_argument("--modality", required=True, choices=MODALITIES)
    parser.add_argument("--activity-type", required=True, choices=ACTIVITY_TYPES)
    add_workload_quantity_options(parser)
    parser.add_argument("--metadata", default=None, help="Arbitrary JSON object.")
    parser.add_argument(
        "--candidate",
        dest="candidates",
        action="append",
        required=True,
        metavar="PROVIDER:MODEL[:MODEL_VERSION]",
        help="Repeatable. At least 2 required.",
    )
    add_global_options(parser)
    parser.set_defaults(handler=run, renderer=render)


def run(args: argparse.Namespace, client: AIClient) -> CompareResult:
    return client.compare.create(
        modality=args.modality,
        activity_type=args.activity_type,
        candidates=parse_candidates(args.candidates),
        **workload_quantity_kwargs(args),
        metadata=parse_metadata(args.metadata),
    )


def render(result: CompareResult, output: str) -> None:
    if output == "json":
        print_json(result)
        return
    print(f"Comparison ID: {result.comparison_id}")
    render_comparison_results(result.results)
    if result.request_id:
        print(f"Request ID: {result.request_id}")
