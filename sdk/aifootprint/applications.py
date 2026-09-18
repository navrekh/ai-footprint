"""Applications resource - maps to POST/GET/PATCH /v1/applications[/{id}]."""

from __future__ import annotations

from ._transport import Transport
from .models import Application, ApplicationList


class ApplicationsResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        environment: str | None = None,
        project_id: str | None = None,
    ) -> Application:
        """`project_id` is required when the client is authenticated
        with an organization-level API key, and optional (must match the
        key's own project) for a project-scoped key.
        """
        data, request_id = self._transport.request(
            "POST",
            "/v1/applications",
            json_body={
                "name": name,
                "description": description,
                "environment": environment,
                "project_id": project_id,
            },
        )
        result = Application.model_validate(data)
        result.request_id = request_id
        return result

    def get(self, application_id: str) -> Application:
        data, request_id = self._transport.request(
            "GET", f"/v1/applications/{application_id}"
        )
        result = Application.model_validate(data)
        result.request_id = request_id
        return result

    def list(
        self, *, project_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> ApplicationList:
        """A project-scoped key is hard-limited to its own project
        regardless of `project_id`; an organization-level key may filter
        by project.
        """
        data, request_id = self._transport.request(
            "GET",
            "/v1/applications",
            params={"project": project_id, "limit": limit, "offset": offset},
        )
        result = ApplicationList.model_validate(data)
        result.request_id = request_id
        return result

    def update(
        self,
        application_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        environment: str | None = None,
    ) -> Application:
        data, request_id = self._transport.request(
            "PATCH",
            f"/v1/applications/{application_id}",
            json_body={
                "name": name,
                "description": description,
                "status": status,
                "environment": environment,
            },
        )
        result = Application.model_validate(data)
        result.request_id = request_id
        return result
