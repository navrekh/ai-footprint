"""API keys resource - maps to POST/GET /v1/api-keys and
POST /v1/api-keys/{id}/revoke.
"""

from __future__ import annotations

from datetime import datetime

from ._transport import Transport
from .models import ApiKey, ApiKeyCreated, ApiKeyList


class ApiKeysResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        name: str,
        project_id: str | None = None,
        expires_at: datetime | None = None,
    ) -> ApiKeyCreated:
        """Returns the full raw key exactly once, in `result.key` - it
        is never retrievable again afterward. Omit `project_id` for an
        organization-level key.
        """
        data, request_id = self._transport.request(
            "POST",
            "/v1/api-keys",
            json_body={"name": name, "project_id": project_id, "expires_at": expires_at},
        )
        result = ApiKeyCreated.model_validate(data)
        result.request_id = request_id
        return result

    def list(self, *, limit: int = 50, offset: int = 0) -> ApiKeyList:
        """Never returns the raw key or its hash - only id, prefix, and metadata."""
        data, request_id = self._transport.request(
            "GET", "/v1/api-keys", params={"limit": limit, "offset": offset}
        )
        result = ApiKeyList.model_validate(data)
        result.request_id = request_id
        return result

    def revoke(self, api_key_id: str) -> ApiKey:
        """Immediately and irreversibly revokes the key; it can no
        longer authenticate.
        """
        data, request_id = self._transport.request(
            "POST", f"/v1/api-keys/{api_key_id}/revoke"
        )
        result = ApiKey.model_validate(data)
        result.request_id = request_id
        return result
