"""Command registration. Each module exposes `register(subparsers)`,
which attaches its own `handler`/`renderer` pair to `args` via
`set_defaults` - `cli.py`'s `main()` never needs a separate dispatch
table keyed by command name.
"""

from __future__ import annotations

import argparse

from . import benchmarks, compare, estimate, event, usage


def register_all(subparsers: argparse._SubParsersAction) -> None:
    event.register(subparsers)
    estimate.register(subparsers)
    usage.register(subparsers)
    compare.register(subparsers)
    benchmarks.register(subparsers)
