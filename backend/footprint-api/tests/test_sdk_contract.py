"""Contract-drift test between the backend's live OpenAPI surface and the
Python SDK's implemented HTTP calls (Sprint 5B, Step 16).

This parses the SDK's source with `ast` rather than importing the
`aifootprint` package, so this test has no dependency on the SDK's own
runtime dependencies (httpx, pydantic) being installed in this project's
environment. The relationship stays one-directional: the backend verifies
the SDK against its own live contract; the SDK itself never imports
anything from the backend.

If this test starts failing:
- the backend added/removed/renamed a route and the SDK needs a matching
  update (see ``sdk/aifootprint/*.py``), or
- the SDK's source no longer matches what it claims to call, which is a
  real bug rather than a stale test.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app

SDK_DIR = Path(__file__).resolve().parents[3] / "sdk" / "aifootprint"

# Resource modules that issue HTTP calls via `self._transport.request(...)`.
# `client.py` is included because `AIClient.health()` calls `GET /health`
# directly rather than through a resource object.
SDK_MODULES = [
    "organizations.py",
    "projects.py",
    "applications.py",
    "api_keys.py",
    "estimates.py",
    "events.py",
    "batch.py",
    "workloads.py",
    "usage.py",
    "compare.py",
    "benchmarks.py",
    "registry.py",
    "client.py",
]

# Backend routes intentionally not exposed as a typed SDK method. Any
# backend route missing from the SDK's source AND missing from this set
# fails the test below - this is the "no silent staleness" guarantee.
BACKEND_ROUTES_WITHOUT_SDK_COVERAGE: set[tuple[str, str]] = set()


def _template_from_joined_str(node: ast.JoinedStr) -> str:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant):
            parts.append(str(value.value))
        elif isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name):
            parts.append("{" + value.value.id + "}")
        else:
            raise AssertionError(f"Unsupported f-string path expression: {ast.dump(value)}")
    return "".join(parts)


def _extract_sdk_routes() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for filename in SDK_MODULES:
        source = (SDK_DIR / filename).read_text()
        tree = ast.parse(source, filename=filename)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "request"):
                continue
            if not (isinstance(func.value, ast.Attribute) and func.value.attr == "_transport"):
                continue
            if len(node.args) < 2:
                continue
            method_node, path_node = node.args[0], node.args[1]
            if not isinstance(method_node, ast.Constant):
                continue
            method = method_node.value
            if isinstance(path_node, ast.Constant):
                path = path_node.value
            elif isinstance(path_node, ast.JoinedStr):
                path = _template_from_joined_str(path_node)
            else:
                raise AssertionError(
                    f"{filename}: unsupported path expression {ast.dump(path_node)}"
                )
            routes.add((method, path))
    return routes


def _extract_backend_routes() -> set[tuple[str, str]]:
    schema = app.openapi()
    routes: set[tuple[str, str]] = set()
    for path, methods in schema["paths"].items():
        for method in methods:
            if method.lower() in ("get", "post", "patch", "put", "delete"):
                routes.add((method.upper(), path))
    return routes


def test_every_sdk_call_targets_a_route_that_actually_exists_on_the_backend() -> None:
    sdk_routes = _extract_sdk_routes()
    backend_routes = _extract_backend_routes()
    unknown = sdk_routes - backend_routes
    assert not unknown, (
        f"SDK calls route(s) that do not exist on the backend: {sorted(unknown)}. "
        "The SDK is out of sync with the API contract."
    )


def test_every_backend_route_is_covered_by_the_sdk_or_explicitly_excluded() -> None:
    sdk_routes = _extract_sdk_routes()
    backend_routes = _extract_backend_routes()
    uncovered = backend_routes - sdk_routes - BACKEND_ROUTES_WITHOUT_SDK_COVERAGE
    assert not uncovered, (
        f"Backend route(s) with no SDK method and no documented exclusion: "
        f"{sorted(uncovered)}. Either add SDK coverage in sdk/aifootprint/ or "
        "add the route to BACKEND_ROUTES_WITHOUT_SDK_COVERAGE with a reason."
    )


def test_sdk_covers_every_public_registry_and_resource_route() -> None:
    """A stronger, explicit sanity check alongside the two structural
    tests above: pins down the exact route count so a route silently
    disappearing from either side (without the set arithmetic somehow
    still balancing) cannot pass unnoticed.
    """
    sdk_routes = _extract_sdk_routes()
    backend_routes = _extract_backend_routes()
    assert sdk_routes == backend_routes
    assert len(backend_routes) >= 30
