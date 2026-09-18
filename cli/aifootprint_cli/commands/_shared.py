"""Argument-parsing helpers shared by more than one command module.

Nothing here calls the SDK or performs I/O beyond argparse - it only
turns CLI-supplied strings into the plain Python values the SDK's
resource methods already accept (see sdk/aifootprint/estimates.py's
`build_workload_body` for the exact field set this mirrors).
"""

from __future__ import annotations

import argparse
import json

from ..exit_codes import CliUsageError

MODALITIES = ["text", "image", "video", "audio", "coding", "agent", "other"]

ACTIVITY_TYPES = [
    "text_generation",
    "text_reasoning",
    "image_generation",
    "image_editing",
    "image_enhancement",
    "video_generation",
    "audio_generation",
    "speech_to_text",
    "vision",
    "code_generation",
    "code_review",
    "debugging",
    "test_generation",
    "code_refactoring",
    "coding_agent",
    "embedding",
    "rag",
    "classification",
    "agent_workflow",
]


def add_global_options(parser: argparse.ArgumentParser) -> None:
    """--api-key/--base-url/--output on every leaf command (not the top-
    level parser) so they can be written either before or after the
    command name is not required - only after, which keeps the parser
    simple and matches `git <command> --flag` conventions.
    """
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=None,
        help="API key (overrides AIFOOTPRINT_API_KEY and local configuration).",
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        default=None,
        help="API base URL (overrides AIFOOTPRINT_BASE_URL and local configuration).",
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )


def add_workload_quantity_options(parser: argparse.ArgumentParser) -> None:
    """The workload quantity fields shared by `event`, `estimate`, and
    `compare` - exactly WorkloadInput's optional quantity fields
    (backend/footprint-api/app/schemas/workload.py). No field is added
    here that the API does not already accept.
    """
    parser.add_argument("--input-tokens", type=int, default=None)
    parser.add_argument("--output-tokens", type=int, default=None)
    parser.add_argument("--input-characters", type=int, default=None)
    parser.add_argument("--output-characters", type=int, default=None)
    parser.add_argument("--image-count", type=int, default=None)
    parser.add_argument("--image-width", type=int, default=None)
    parser.add_argument("--image-height", type=int, default=None)
    parser.add_argument("--video-seconds", type=float, default=None)
    parser.add_argument("--video-resolution", type=str, default=None)
    parser.add_argument("--audio-seconds", type=float, default=None)
    parser.add_argument("--tool-calls", type=int, default=None)
    parser.add_argument("--duration-seconds", type=float, default=None)
    parser.add_argument("--duration-ms", type=float, default=None)


def workload_quantity_kwargs(args: argparse.Namespace) -> dict:
    return {
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "input_characters": args.input_characters,
        "output_characters": args.output_characters,
        "image_count": args.image_count,
        "image_width": args.image_width,
        "image_height": args.image_height,
        "video_seconds": args.video_seconds,
        "video_resolution": args.video_resolution,
        "audio_seconds": args.audio_seconds,
        "tool_calls": args.tool_calls,
        "duration_seconds": args.duration_seconds,
        "duration_ms": args.duration_ms,
    }


def parse_metadata(raw: str | None) -> dict | None:
    """`--metadata` is a JSON object string, e.g. '{"customer_tier":
    "enterprise"}' - never a place to put prompt/response content (see
    the CLI README's Privacy section).
    """
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliUsageError(f"--metadata must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CliUsageError('--metadata must be a JSON object, e.g. \'{"key": "value"}\'.')
    return value


def parse_candidate(raw: str) -> dict:
    """`provider:model` or `provider:model:model_version` - same shape
    client.compare.create()/client.benchmarks.run() already accept.
    """
    parts = raw.split(":", 2)
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise CliUsageError(
            f"Invalid --candidate {raw!r}: expected 'provider:model' or "
            "'provider:model:model_version'."
        )
    candidate = {"provider": parts[0], "model": parts[1]}
    if len(parts) == 3 and parts[2]:
        candidate["model_version"] = parts[2]
    return candidate


def parse_candidates(raw_values: list[str]) -> list[dict]:
    return [parse_candidate(value) for value in raw_values]
