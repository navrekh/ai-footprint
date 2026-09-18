"""The AI Footprint SDK exception hierarchy.

Every exception this SDK raises for an HTTP-level failure is one of the
subclasses below. Normal SDK users should never see a raw `httpx`
exception or an unhandled `KeyError`/`json.JSONDecodeError` from a
malformed response - those are always converted here.

Mapping from the backend's actual error contract
(``{"error": {"code", "message", "request_id"}}``, documented in
``backend/footprint-api/README.md``'s "Errors" section) to SDK
exceptions is by HTTP status code, not by guessing at error-code
semantics, since status codes are the stable, versioned part of the
contract:

* 401 -> `AuthenticationError`
* 403 -> `AuthorizationError`
* 404 -> `NotFoundError`
* 400, 422 -> `ValidationError`
* 409 -> `ConflictError` (not currently returned by any endpoint as of
  Sprint 5B - included for forward compatibility with the documented
  SDK exception hierarchy; see the SDK README for the current status).
* 429 -> `RateLimitError`
* 5xx, and any other unrecognized status -> `APIError`
* network/timeout failures that never reach the server -> `TransportError`
"""

from __future__ import annotations


class AIFootprintError(Exception):
    """Base class for every exception this SDK raises."""


class TransportError(AIFootprintError):
    """The request never completed - a network failure, connection
    error, or timeout. No HTTP response was received, so there is no
    status code, error code, or request_id to attach.
    """


class APIError(AIFootprintError):
    """The server returned an HTTP error response.

    Carries the diagnostics a developer needs to report or debug an
    issue, without ever including the API key or other request headers.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [self.message, f"(status={self.status_code}"]
        if self.code:
            parts.append(f", code={self.code}")
        if self.request_id:
            parts.append(f", request_id={self.request_id}")
        parts.append(")")
        return " ".join([parts[0], "".join(parts[1:])])


class AuthenticationError(APIError):
    """401 - the API key is missing, unknown, malformed, revoked, or expired."""


class AuthorizationError(APIError):
    """403 - the authenticated API key is not permitted to perform this action."""


class NotFoundError(APIError):
    """404 - the requested resource does not exist, or is not visible to
    the authenticated caller (the backend deliberately never
    distinguishes the two - see docs/PRD.md section 13).
    """


class ValidationError(APIError):
    """400 or 422 - the request was malformed or semantically invalid
    (e.g. a missing required parameter, an incompatible activity_type/
    modality pair, or an unsupported model).
    """


class ConflictError(APIError):
    """409 - reserved for a future conflicting-state response. No
    current AI Footprint endpoint returns this status; idempotent replay
    on POST /v1/events returns 200, not 409.
    """


class RateLimitError(APIError):
    """429 - reserved for a future rate limiter. As of Sprint 5B the
    backend does not enforce rate limiting (see backend README's Known
    Limitations), but this exception exists so SDK error-handling code
    written against it keeps working once the backend does.
    """
