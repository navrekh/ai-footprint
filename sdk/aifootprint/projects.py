"""Projects resource - maps to POST/GET/PATCH /v1/projects[/{id}]."""

from __future__ import annotations

from ._transport import Transport
from .models import Project, ProjectList


class ProjectsResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(self, *, name: str, description: str | None = None) -> Project:
        data, request_id = self._transport.request(
            "POST",
            "/v1/projects",
            json_body={"name": name, "description": description},
        )
        result = Project.model_validate(data)
        result.request_id = request_id
        return result

    def get(self, project_id: str) -> Project:
        data, request_id = self._transport.request("GET", f"/v1/projects/{project_id}")
        result = Project.model_validate(data)
        result.request_id = request_id
        return result

    def list(self, *, limit: int = 50, offset: int = 0) -> ProjectList:
        """Limit/offset-paginated list of every project in the
        authenticated organization. `limit` is 1-200.
        """
        data, request_id = self._transport.request(
            "GET", "/v1/projects", params={"limit": limit, "offset": offset}
        )
        result = ProjectList.model_validate(data)
        result.request_id = request_id
        return result

    def update(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Project:
        data, request_id = self._transport.request(
            "PATCH",
            f"/v1/projects/{project_id}",
            json_body={"name": name, "description": description, "status": status},
        )
        result = Project.model_validate(data)
        result.request_id = request_id
        return result
