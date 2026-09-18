"""Shared OpenAPI error-response documentation (sprint 5A, FRD section 36.6).

FastAPI can only auto-document a route's success response and its own
422 validation-error response. Every domain error this API actually
returns (`{"error": {"code","message","request_id"}}`, raised as an
`AppError` subclass and rendered by the global exception handler in
app/main.py) is otherwise invisible to the generated OpenAPI schema,
since FastAPI has no way to introspect a global exception handler. Every
route that can raise one of these must declare it explicitly via
`error_responses(...)` in its `responses=` kwarg for it to appear in
`/openapi.json` and Swagger UI.

This module is documentation-only: it does not change any route's
runtime behavior, only what is described about it.
"""

from typing import Any

from app.core.errors import STATUS_BY_CODE, ErrorCode

EXAMPLE_REQUEST_ID = "req_0123456789abcdef0123456789abcdef"

# Matches FastAPI's own `responses` parameter type exactly, so the
# helper's output can be passed straight through without a mypy mismatch.
OpenAPIResponses = dict[int | str, dict[str, Any]]

_EXAMPLE_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_REQUEST: "The request could not be processed as submitted.",
    ErrorCode.INVALID_API_KEY: "The provided API key is invalid or revoked.",
    ErrorCode.API_KEY_EXPIRED: "The provided API key has expired.",
    ErrorCode.UNAUTHORIZED: "Authentication is required for this endpoint.",
    ErrorCode.FORBIDDEN: "This API key is scoped to a different project.",
    ErrorCode.PROVIDER_NOT_FOUND: "Provider 'unknown-provider' was not found.",
    ErrorCode.MODEL_NOT_FOUND: "Model 'unknown-model' was not found for provider 'openai'.",
    ErrorCode.MODEL_NOT_SUPPORTED: "The requested model is not currently supported.",
    ErrorCode.INVALID_WORKLOAD: (
        "activity_type 'image_generation' is not valid for modality 'text'."
    ),
    ErrorCode.MISSING_PARAMETER: "Missing required parameter: project_id",
    ErrorCode.METHODOLOGY_UNAVAILABLE: (
        "No approved methodology data is available for this workload."
    ),
    ErrorCode.RATE_LIMITED: "Rate limit exceeded.",
    ErrorCode.NOT_FOUND: "Resource not found.",
    ErrorCode.APPLICATION_NOT_FOUND: "Application not found.",
    ErrorCode.APPLICATION_PROJECT_MISMATCH: (
        "The application does not belong to the target project."
    ),
    ErrorCode.INVALID_DATE_RANGE: "'from' must be earlier than 'to'.",
    ErrorCode.BENCHMARK_NOT_FOUND: "Benchmark 'does-not-exist' was not found.",
    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred.",
}

_STATUS_DESCRIPTIONS: dict[int, str] = {
    400: "Bad request - invalid input.",
    401: "Authentication is missing, invalid, or expired.",
    403: "The authenticated API key is not permitted to perform this action.",
    404: (
        "The requested resource does not exist, or does not belong to the caller's "
        "organization/project."
    ),
    422: "The request was well-formed but is semantically invalid.",
    429: "Too many requests.",
    500: "An unexpected server error occurred.",
}


def _error_example(code: ErrorCode) -> dict[str, Any]:
    return {
        "error": {
            "code": code.value,
            "message": _EXAMPLE_MESSAGES.get(
                code, f"{code.value.replace('_', ' ').capitalize()}."
            ),
            "request_id": EXAMPLE_REQUEST_ID,
        }
    }


def error_responses(*codes: ErrorCode) -> OpenAPIResponses:
    """Builds an OpenAPI `responses=` fragment for the given error codes,
    grouping multiple codes that share an HTTP status into one response
    entry with one example per code (via OpenAPI's `examples` map).
    """
    responses: OpenAPIResponses = {}
    for code in codes:
        status_code = STATUS_BY_CODE[code]
        entry = responses.setdefault(
            status_code,
            {
                "description": _STATUS_DESCRIPTIONS.get(status_code, "Error response."),
                "content": {"application/json": {"examples": {}}},
            },
        )
        entry["content"]["application/json"]["examples"][code.value] = {
            "summary": code.value,
            "value": _error_example(code),
        }
    return responses


# Reused verbatim by almost every authenticated endpoint - the
# get_auth_context dependency can raise any of these three regardless of
# the route's own logic.
AUTH_ERRORS = (
    ErrorCode.UNAUTHORIZED,
    ErrorCode.INVALID_API_KEY,
    ErrorCode.API_KEY_EXPIRED,
)
