"""Workloads resource - read-only history, maps to GET /v1/workloads
(cursor-paginated) and GET /v1/workloads/{id}.
"""

from __future__ import annotations

from datetime import datetime

from ._transport import Transport
from .models import Workload, WorkloadPage


class WorkloadsResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        project_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
        from_: datetime | None = None,
        to: datetime | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> WorkloadPage:
        """Opaque, keyset-paginated (not limit/offset). Pass the
        previous result's `next_cursor` back as `cursor` to fetch the
        next page; `next_cursor=None` means the last page. `limit` is
        1-100.
        """
        data, request_id = self._transport.request(
            "GET",
            "/v1/workloads",
            params={
                "project": project_id,
                "provider": provider,
                "model": model,
                "activity_type": activity_type,
                "from": from_,
                "to": to,
                "cursor": cursor,
                "limit": limit,
            },
        )
        result = WorkloadPage.model_validate(data)
        result.request_id = request_id
        return result

    def get(self, workload_id: str) -> Workload:
        data, request_id = self._transport.request("GET", f"/v1/workloads/{workload_id}")
        result = Workload.model_validate(data)
        result.request_id = request_id
        return result
