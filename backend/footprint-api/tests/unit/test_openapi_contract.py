"""Documentation drift prevention (sprint 5A).

These tests do not test application behavior - they test that the
generated OpenAPI schema, the developer-facing README, and the actual
set of registered routes stay synchronized. This is a direct regression
test for the exact defect found during the sprint 5 audit: /v1/compare
and all three /v1/benchmarks* endpoints existed and were fully tested,
but were simply missing from the README's endpoint table because
nothing enforced the two staying in sync.
"""

import re
from pathlib import Path

from app.main import app

README_PATH = Path(__file__).resolve().parents[2] / "README.md"

# The exact, current set of (method, path) pairs this API exposes. A
# route added or removed without updating this set fails loudly here,
# forcing a deliberate decision (and a README/OpenAPI update) rather
# than silent drift.
EXPECTED_ROUTES = {
    ("GET", "/health"),
    ("POST", "/v1/organizations"),
    ("GET", "/v1/organizations/{organization_id}"),
    ("POST", "/v1/projects"),
    ("GET", "/v1/projects"),
    ("GET", "/v1/projects/{project_id}"),
    ("PATCH", "/v1/projects/{project_id}"),
    ("POST", "/v1/applications"),
    ("GET", "/v1/applications"),
    ("GET", "/v1/applications/{application_id}"),
    ("PATCH", "/v1/applications/{application_id}"),
    ("POST", "/v1/api-keys"),
    ("GET", "/v1/api-keys"),
    ("POST", "/v1/api-keys/{api_key_id}/revoke"),
    ("POST", "/v1/estimate"),
    ("POST", "/v1/events"),
    ("POST", "/v1/batch-estimate"),
    ("GET", "/v1/workloads"),
    ("GET", "/v1/workloads/{workload_id}"),
    ("GET", "/v1/estimates/{estimate_id}"),
    ("GET", "/v1/usage/summary"),
    ("GET", "/v1/usage/by-provider"),
    ("GET", "/v1/usage/by-model"),
    ("GET", "/v1/usage/by-activity"),
    ("GET", "/v1/usage/by-application"),
    ("GET", "/v1/usage/timeseries"),
    ("POST", "/v1/compare"),
    ("GET", "/v1/benchmarks"),
    ("GET", "/v1/benchmarks/{benchmark_id}"),
    ("POST", "/v1/benchmarks/run"),
    ("GET", "/v1/providers"),
    ("GET", "/v1/models"),
    ("GET", "/v1/methodology"),
}

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _actual_routes() -> set[tuple[str, str]]:
    spec = app.openapi()
    routes = set()
    for path, operations in spec["paths"].items():
        for method in operations:
            if method in _HTTP_METHODS:
                routes.add((method.upper(), path))
    return routes


def _normalize(path: str) -> str:
    """Collapses every {param_name} to {id} so a path can be matched
    against README's single, generic {id} placeholder convention
    regardless of the OpenAPI parameter's actual name.
    """
    return re.sub(r"\{[^}]+\}", "{id}", path)


def test_registered_routes_match_the_expected_set():
    actual = _actual_routes()
    missing = EXPECTED_ROUTES - actual
    unexpected = actual - EXPECTED_ROUTES
    assert not missing, f"Routes expected but not registered: {sorted(missing)}"
    assert not unexpected, (
        f"New route(s) registered but not acknowledged in EXPECTED_ROUTES "
        f"(update this test AND README.md's endpoint table): {sorted(unexpected)}"
    )


def test_every_documented_route_appears_in_the_readme():
    readme_text = README_PATH.read_text()
    missing_from_readme = []
    for _method, path in sorted(EXPECTED_ROUTES):
        normalized = _normalize(path)
        if normalized not in readme_text:
            missing_from_readme.append(normalized)
    assert not missing_from_readme, (
        f"Path(s) missing from README.md's endpoint table: {missing_from_readme}"
    )


def test_every_route_has_a_summary_and_description():
    spec = app.openapi()
    undocumented = []
    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            if method not in _HTTP_METHODS:
                continue
            if not operation.get("summary"):
                undocumented.append((method.upper(), path, "summary"))
            if not operation.get("description"):
                undocumented.append((method.upper(), path, "description"))
    assert not undocumented, f"Route(s) missing summary/description: {undocumented}"


def test_every_authenticated_route_documents_an_unauthorized_response():
    """Every route that depends on get_auth_context can raise
    UNAUTHORIZED/INVALID_API_KEY/API_KEY_EXPIRED (401) - a route that
    forgets to declare this via error_responses(*AUTH_ERRORS, ...) would
    otherwise silently disappear from the generated OpenAPI schema's
    error documentation without any test catching it.
    """
    public_routes = {
        ("GET", "/health"),
        ("POST", "/v1/organizations"),
        ("GET", "/v1/providers"),
        ("GET", "/v1/models"),
        ("GET", "/v1/methodology"),
        ("GET", "/v1/benchmarks"),
        ("GET", "/v1/benchmarks/{benchmark_id}"),
    }
    spec = app.openapi()
    missing_401 = []
    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            if method not in _HTTP_METHODS:
                continue
            route = (method.upper(), path)
            if route in public_routes:
                continue
            if "401" not in operation.get("responses", {}):
                missing_401.append(route)
    assert not missing_401, (
        f"Authenticated route(s) missing a documented 401 response: {missing_401}"
    )
