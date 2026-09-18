"""Organizations resource - maps to POST /v1/organizations and
GET /v1/organizations/{id}. There is no list-all-organizations endpoint
(an API key is always scoped to exactly one organization), so no
`.list()` method exists here - it would not correspond to anything the
backend provides.
"""

from __future__ import annotations

from ._transport import Transport
from .models import Organization, OrganizationBootstrap


class OrganizationsResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(self, *, name: str) -> OrganizationBootstrap:
        """Signs up: creates an Organization, a default Project, and a
        first Project-scoped API key, in one unauthenticated call. This
        is the only place besides `client.api_keys.create()` where a raw
        API key is returned - `result.api_key.key` is shown exactly
        once and cannot be retrieved again.
        """
        data, request_id = self._transport.request(
            "POST", "/v1/organizations", json_body={"name": name}
        )
        result = OrganizationBootstrap.model_validate(data)
        result.request_id = request_id
        return result

    def get(self, organization_id: str) -> Organization:
        """Returns the authenticated caller's own organization. Any id
        other than the caller's own returns a NotFoundError - existence
        of another organization is never confirmed or denied.
        """
        data, request_id = self._transport.request(
            "GET", f"/v1/organizations/{organization_id}"
        )
        result = Organization.model_validate(data)
        result.request_id = request_id
        return result
