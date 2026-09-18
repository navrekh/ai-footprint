"""Internal HTTP transport. Not part of the public API - resource
modules (events.py, usage.py, ...) receive a `Transport` instance from
`AIClient` and never construct or import `httpx` themselves.

Kept separate from client.py specifically so resource modules can type-
hint against `Transport` without importing `client.py` (which imports
every resource module to build `AIClient`) - avoids a circular import.
"""

from __future__ import annotations

import json as _json
from datetime import date, datetime
from enum import Enum
from typing import Any

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    TransportError,
    ValidationError,
)

REQUEST_ID_HEADER = "X-Request-ID"

_EXCEPTION_BY_STATUS: dict[int, type[APIError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def _clean(value: Any) -> Any:
    """Recursively converts enums to their `.value` and dates/datetimes
    to ISO 8601 strings, and drops None values from dicts, so callers
    can pass Python-native values (enum members, datetime objects,
    plain dicts) without hand-serializing them. Never invents or
    changes a value's meaning - purely a wire-format transcription.
    """
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if v is not None}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


class Transport:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        timeout: float,
    ) -> None:
        headers = {"Accept": "application/json"}
        if api_key:
            # Sent only ever as the Authorization header, per the
            # backend's bearer-key contract - never as a query
            # parameter, never in the URL path, never logged here.
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(base_url=base_url, timeout=timeout, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any, str | None]:
        clean_params = _clean(params) if params else None
        clean_body = _clean(json_body) if json_body is not None else None

        try:
            response = self._client.request(
                method, path, json=clean_body, params=clean_params
            )
        except httpx.TimeoutException as exc:
            raise TransportError(f"Request to {path} timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise TransportError(f"Network error calling {path}: {exc}") from exc

        request_id = response.headers.get(REQUEST_ID_HEADER)

        if response.status_code >= 400:
            raise _build_api_error(response, request_id)

        if not response.content:
            return {}, request_id

        try:
            return response.json(), request_id
        except _json.JSONDecodeError as exc:
            raise APIError(
                f"Server returned a non-JSON response from {path}.",
                status_code=response.status_code,
                request_id=request_id,
            ) from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Transport:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _build_api_error(response: httpx.Response, request_id: str | None) -> APIError:
    message = f"Request failed with status {response.status_code}."
    code: str | None = None
    try:
        body = response.json()
        error = body.get("error") if isinstance(body, dict) else None
        if isinstance(error, dict):
            message = error.get("message", message)
            code = error.get("code")
            request_id = error.get("request_id", request_id)
    except _json.JSONDecodeError:
        pass

    exception_cls = _EXCEPTION_BY_STATUS.get(response.status_code, APIError)
    return exception_cls(
        message,
        status_code=response.status_code,
        code=code,
        request_id=request_id,
    )
