"""The `aifootprint` CLI entry point.

Architectural boundary (Sprint 7 FRD section 39.2/39.13, non-negotiable):

    aifootprint CLI -> Python SDK (aifootprint) -> existing REST API

This module - and every module under `commands/` - imports `AIClient`
from the `aifootprint` package and calls its resource methods
(`client.events.create()`, `client.usage.summary()`, ...) exclusively.
Nothing in this package imports `httpx`, builds an `Authorization`
header, or parses a raw HTTP error response: `AIClient`/`Transport`
(sdk/aifootprint/_transport.py) remain the sole HTTP/authentication
boundary, and `aifootprint.exceptions` remains the sole error hierarchy
(see exit_codes.py). This is enforced structurally, not just by
convention - see tests/test_sdk_boundary.py.
"""

from __future__ import annotations

import argparse
import sys

from aifootprint import AIClient, AIFootprintError, APIError

from . import __version__
from .commands import register_all
from .config import resolve_api_key, resolve_base_url
from .exit_codes import (
    EXIT_CONFIGURATION_ERROR,
    EXIT_SUCCESS,
    EXIT_UNEXPECTED_ERROR,
    CliUsageError,
    ConfigurationError,
    exit_code_for,
)

PROG = "aifootprint"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Command-line client for the AI Footprint API.",
    )
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}")
    # Not required at the top level: `aifootprint` with no arguments
    # prints help and exits 0 (exploration, not an error). The nested
    # `usage`/`benchmarks` subparsers ARE required - naming only the
    # group without an action is unambiguously incomplete there.
    subparsers = parser.add_subparsers(dest="command", required=False)
    register_all(subparsers)
    return parser


def _print_error(exc: BaseException) -> None:
    """Never includes an API key: `APIError`/`TransportError` messages
    come from the SDK, which itself never embeds request headers in an
    exception (see sdk/aifootprint/exceptions.py's module docstring).
    """
    if isinstance(exc, APIError):
        parts = [exc.message]
        if exc.code:
            parts.append(f"[{exc.code}]")
        print(f"Error: {' '.join(parts)}", file=sys.stderr)
        if exc.request_id:
            print(f"Request ID: {exc.request_id}", file=sys.stderr)
    elif isinstance(exc, (CliUsageError, ConfigurationError, AIFootprintError)):
        print(f"Error: {exc}", file=sys.stderr)
    else:
        print(f"Unexpected error: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return EXIT_SUCCESS
        return code if isinstance(code, int) else EXIT_UNEXPECTED_ERROR

    handler = getattr(args, "handler", None)
    renderer = getattr(args, "renderer", None)
    if handler is None or renderer is None:
        parser.print_help()
        return EXIT_SUCCESS

    try:
        api_key = resolve_api_key(getattr(args, "api_key", None))
        base_url = resolve_base_url(getattr(args, "base_url", None))
    except ConfigurationError as exc:
        _print_error(exc)
        return EXIT_CONFIGURATION_ERROR

    client = AIClient(api_key=api_key, base_url=base_url)
    try:
        result = handler(args, client)
    except (CliUsageError, ConfigurationError, AIFootprintError) as exc:
        _print_error(exc)
        return exit_code_for(exc)
    finally:
        client.close()

    renderer(result, args.output)
    return EXIT_SUCCESS


def run() -> None:
    sys.exit(main())
