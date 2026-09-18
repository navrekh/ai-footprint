"""Sprint 7 FRD section 39.13's SDK boundary, verified structurally
rather than by convention alone: no CLI module may import `httpx` (or
any other HTTP client library) or construct its own bearer-token
header. Parses source with `ast` rather than importing the package, so
this test would also catch a forbidden import even if it were never
exercised at runtime.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "aifootprint_cli"

FORBIDDEN_MODULES = {"httpx", "requests", "urllib3", "http.client", "aiohttp"}


def _all_python_files() -> list[Path]:
    return sorted(PACKAGE_DIR.rglob("*.py"))


def _imported_module_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_no_cli_module_imports_an_http_client_library():
    offenders = []
    for path in _all_python_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        imported = _imported_module_names(tree)
        forbidden_hit = imported & FORBIDDEN_MODULES
        if forbidden_hit:
            offenders.append((path.relative_to(PACKAGE_DIR), forbidden_hit))
    assert not offenders, (
        f"CLI module(s) importing an HTTP client library directly: {offenders}. "
        "All API communication must go through the aifootprint SDK's AIClient."
    )


def test_no_cli_module_builds_an_authorization_header_literal():
    """A second bearer-token implementation would most plausibly show up
    as a literal "Authorization"/"Bearer" string outside of comments -
    `ast` only walks real string constants, so a docstring/comment
    mentioning "Bearer" (as several modules' docstrings legitimately do,
    to explain *why* they don't build one) can never trip this check.
    """
    offenders = []
    for path in _all_python_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.strip().lower() in {"authorization", "bearer"}:
                    offenders.append(path.relative_to(PACKAGE_DIR))
    assert not offenders, (
        f"CLI module(s) with a literal Authorization/Bearer string: {offenders}. "
        "AIClient/Transport already build this header - see sdk/aifootprint/_transport.py."
    )


def test_command_modules_only_call_the_sdk_client_for_api_access():
    """Every `commands/*.py` module must import `AIClient` (or nothing
    API-related at all, for pure argument-parsing helpers) - never a
    lower-level transport primitive.
    """
    commands_dir = PACKAGE_DIR / "commands"
    for path in sorted(commands_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue  # shared argument-parsing helpers, no API access
        tree = ast.parse(path.read_text(), filename=str(path))
        imported = _imported_module_names(tree)
        assert "aifootprint" in imported, (
            f"{path.name} does not import the aifootprint SDK at all - "
            "every command module must use AIClient for API access."
        )
