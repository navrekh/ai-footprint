"""`aifootprint benchmarks <subcommand>` - the existing benchmark
endpoints, through `AIClient.benchmarks.*` only (Sprint 7 FRD section
39.8). `list`/`get` require no API key (public reference data, same as
the backend); `run` requires one but reads no tenant-owned data.
"""

from __future__ import annotations

import argparse

from aifootprint import AIClient
from aifootprint.models import BenchmarkDefinition, BenchmarkList, BenchmarkRunResult, ResultBase

from ..output import print_json
from ._comparison import render_comparison_results
from ._shared import ACTIVITY_TYPES, MODALITIES, add_global_options, parse_candidates


def register(subparsers: argparse._SubParsersAction) -> None:
    benchmarks_parser = subparsers.add_parser(
        "benchmarks", help="Standardized, versioned workload definitions"
    )
    benchmarks_subparsers = benchmarks_parser.add_subparsers(
        dest="benchmarks_command", required=True
    )

    list_parser = benchmarks_subparsers.add_parser("list", help="List benchmark definitions")
    list_parser.add_argument("--activity-type", default=None, choices=ACTIVITY_TYPES)
    list_parser.add_argument("--modality", default=None, choices=MODALITIES)
    add_global_options(list_parser)
    list_parser.set_defaults(handler=run_list, renderer=render)

    get_parser = benchmarks_subparsers.add_parser("get", help="Get one benchmark definition")
    get_parser.add_argument("benchmark_id")
    add_global_options(get_parser)
    get_parser.set_defaults(handler=run_get, renderer=render)

    run_parser = benchmarks_subparsers.add_parser(
        "run",
        help="Execute a benchmark against candidates (POST /v1/benchmarks/run)",
        description=(
            "Evaluates the benchmark's fixed workload independently against each "
            "candidate, exactly like compare. Results are never ranked or scored."
        ),
    )
    run_parser.add_argument("benchmark_id")
    run_parser.add_argument(
        "--candidate",
        dest="candidates",
        action="append",
        required=True,
        metavar="PROVIDER:MODEL[:MODEL_VERSION]",
        help="Repeatable. At least 2 required.",
    )
    add_global_options(run_parser)
    run_parser.set_defaults(handler=run_run, renderer=render)


def run_list(args: argparse.Namespace, client: AIClient) -> BenchmarkList:
    return client.benchmarks.list(activity_type=args.activity_type, modality=args.modality)


def run_get(args: argparse.Namespace, client: AIClient) -> BenchmarkDefinition:
    return client.benchmarks.get(args.benchmark_id)


def run_run(args: argparse.Namespace, client: AIClient) -> BenchmarkRunResult:
    return client.benchmarks.run(args.benchmark_id, parse_candidates(args.candidates))


def render(result: ResultBase, output: str) -> None:
    if output == "json":
        print_json(result)
        return
    if isinstance(result, BenchmarkList):
        _render_list(result)
    elif isinstance(result, BenchmarkDefinition):
        _render_definition(result)
    elif isinstance(result, BenchmarkRunResult):
        print(f"Benchmark: {result.benchmark_id} (version {result.benchmark_version})")
        render_comparison_results(result.results)
    if result.request_id:
        print(f"Request ID: {result.request_id}")


def _render_list(result: BenchmarkList) -> None:
    if not result.items:
        print("(no benchmarks)")
        return
    for item in result.items:
        print(f"- {item.benchmark_id} (v{item.version}) - {item.name}")
        print(f"    {item.activity_type} / {item.modality}")


def _render_definition(item: BenchmarkDefinition) -> None:
    print(f"Benchmark ID: {item.benchmark_id}")
    print(f"Name: {item.name}")
    print(f"Version: {item.version}")
    print(f"Description: {item.description}")
    print(f"Activity type: {item.activity_type}")
    print(f"Modality: {item.modality}")
    if item.parameters:
        print("Parameters:")
        for key, value in item.parameters.items():
            print(f"  {key}: {value}")
