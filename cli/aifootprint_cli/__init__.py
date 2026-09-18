"""aifootprint-cli - the command-line client for the AI Footprint API.

This package contains no estimation, methodology, or ranking logic of
its own. Every command is a thin wrapper around the existing
`aifootprint` Python SDK (see cli.py's module docstring for the
architectural boundary).

`__version__` is the single source of truth for the CLI's version: it
is read by `pyproject.toml` (`[tool.setuptools.dynamic]`) rather than
being duplicated there, and by the `--version` flag and the Sprint 6
client-context metadata (aifootprint_cli/context.py) rather than being
hard-coded a second time in either place.
"""

__version__ = "0.1.0"
