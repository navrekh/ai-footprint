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

# What each error.code actually means - the single source of truth for
# per-code documentation. Surfaced per-route below as each OpenAPI
# example's `description` (the natural, schema-validation-free way to
# document enum-like values that, unlike ActivityType/Modality/
# UsageGranularity, are never themselves a Pydantic model field -
# ErrorDetail.code is typed as plain `str`, so ErrorCode is never a
# referenced OpenAPI component schema and a docstring on the enum class
# itself would not appear in /openapi.json). Also mirrored in
# backend/footprint-api/README.md's "Errors" table - keep both in sync.
CODE_DESCRIPTIONS: dict[ErrorCode, str] = {
    ErrorCode.INVALID_REQUEST: (
        "Malformed or oversized request, e.g. a batch or candidate-list limit exceeded."
    ),
    ErrorCode.INVALID_API_KEY: "The API key is unknown, malformed, or revoked.",
    ErrorCode.API_KEY_EXPIRED: "The key was valid but its expires_at has passed.",
    ErrorCode.UNAUTHORIZED: "No Authorization header was supplied.",
    ErrorCode.FORBIDDEN: "A project-scoped key explicitly targeted a different project.",
    ErrorCode.PROVIDER_NOT_FOUND: "The requested provider is not registered.",
    ErrorCode.MODEL_NOT_FOUND: (
        "The requested model (or model_version) is not registered for that provider."
    ),
    ErrorCode.MODEL_NOT_SUPPORTED: (
        "The model is deprecated, or does not support the requested modality."
    ),
    ErrorCode.INVALID_WORKLOAD: (
        "e.g. an activity_type/modality mismatch, or a zero-quantity text workload."
    ),
    ErrorCode.MISSING_PARAMETER: (
        "A required parameter was omitted (e.g. project_id for an organization-level key)."
    ),
    ErrorCode.METHODOLOGY_UNAVAILABLE: (
        "Reserved; not currently raised - see the insufficient_data metric status instead."
    ),
    ErrorCode.RATE_LIMITED: "Reserved for a future rate limiter; not currently enforced.",
    ErrorCode.NOT_FOUND: (
        "A generic resource does not exist, or belongs to another tenant - deliberately "
        "opaque, never distinguishing the two."
    ),
    ErrorCode.APPLICATION_NOT_FOUND: (
        "The application does not exist anywhere the caller's organization can see."
    ),
    ErrorCode.APPLICATION_PROJECT_MISMATCH: (
        "The application exists in the caller's organization but a different project."
    ),
    ErrorCode.INVALID_DATE_RANGE: (
        "from is after to, or the requested range/granularity would exceed bounds."
    ),
    ErrorCode.BENCHMARK_NOT_FOUND: "The requested benchmark_id is not a known definition.",
    ErrorCode.INTERNAL_ERROR: "An unhandled server error; never leaks a stack trace.",
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
    entry with one example per code (via OpenAPI's `examples` map). Each
    example's `description` explains what that specific code means -
    see CODE_DESCRIPTIONS.
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
            "description": CODE_DESCRIPTIONS.get(code, ""),
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
