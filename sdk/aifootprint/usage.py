"""Usage resource - maps to the six GET /v1/usage/* endpoints. All
aggregation happens server-side; this module only sends filters and
parses typed results - see docs/METHODOLOGY.md and the backend README
for the coverage/range semantics these responses preserve.
"""

from __future__ import annotations

from datetime import datetime

from ._transport import Transport
from .models import (
    UsageByActivityResult,
    UsageByApplicationResult,
    UsageByModelResult,
    UsageByProviderResult,
    UsageSummary,
    UsageTimeseriesResult,
)


class UsageResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def summary(
        self,
        *,
        from_: datetime | None = None,
        to: datetime | None = None,
        project_id: str | None = None,
        application_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
    ) -> UsageSummary:
        """Defaults to the trailing 30 days when `from_`/`to` are omitted."""
        data, request_id = self._transport.request(
            "GET",
            "/v1/usage/summary",
            params=self._filters(
                from_, to, project_id, application_id, provider, model, activity_type
            ),
        )
        result = UsageSummary.model_validate(data)
        result.request_id = request_id
        return result

    def by_provider(
        self,
        *,
        from_: datetime | None = None,
        to: datetime | None = None,
        project_id: str | None = None,
        application_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> UsageByProviderResult:
        params = self._filters(
            from_, to, project_id, application_id, provider, model, activity_type
        )
        params.update({"limit": limit, "offset": offset})
        data, request_id = self._transport.request("GET", "/v1/usage/by-provider", params=params)
        result = UsageByProviderResult.model_validate(data)
        result.request_id = request_id
        return result

    def by_model(
        self,
        *,
        from_: datetime | None = None,
        to: datetime | None = None,
        project_id: str | None = None,
        application_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> UsageByModelResult:
        params = self._filters(
            from_, to, project_id, application_id, provider, model, activity_type
        )
        params.update({"limit": limit, "offset": offset})
        data, request_id = self._transport.request("GET", "/v1/usage/by-model", params=params)
        result = UsageByModelResult.model_validate(data)
        result.request_id = request_id
        return result

    def by_activity(
        self,
        *,
        from_: datetime | None = None,
        to: datetime | None = None,
        project_id: str | None = None,
        application_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> UsageByActivityResult:
        params = self._filters(
            from_, to, project_id, application_id, provider, model, activity_type
        )
        params.update({"limit": limit, "offset": offset})
        data, request_id = self._transport.request("GET", "/v1/usage/by-activity", params=params)
        result = UsageByActivityResult.model_validate(data)
        result.request_id = request_id
        return result

    def by_application(
        self,
        *,
        from_: datetime | None = None,
        to: datetime | None = None,
        project_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> UsageByApplicationResult:
        """Excludes workloads with no application (never a synthetic
        "unassigned" bucket). Unlike the other usage breakdowns, this
        endpoint does not accept an `application` filter - use
        `summary()` for that.
        """
        params = self._filters(from_, to, project_id, None, provider, model, activity_type)
        params.pop("application", None)
        params.update({"limit": limit, "offset": offset})
        data, request_id = self._transport.request("GET", "/v1/usage/by-application", params=params)
        result = UsageByApplicationResult.model_validate(data)
        result.request_id = request_id
        return result

    def timeseries(
        self,
        *,
        granularity: str = "day",
        from_: datetime | None = None,
        to: datetime | None = None,
        project_id: str | None = None,
        application_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        activity_type: str | None = None,
    ) -> UsageTimeseriesResult:
        """`granularity` is "day", "week", or "month". Bounded to a
        maximum of 400 buckets rather than paginated - narrow the date
        range or use a coarser granularity if the request is rejected
        with a ValidationError.
        """
        params = self._filters(
            from_, to, project_id, application_id, provider, model, activity_type
        )
        params["granularity"] = granularity
        data, request_id = self._transport.request("GET", "/v1/usage/timeseries", params=params)
        result = UsageTimeseriesResult.model_validate(data)
        result.request_id = request_id
        return result

    @staticmethod
    def _filters(
        from_: datetime | None,
        to: datetime | None,
        project_id: str | None,
        application_id: str | None,
        provider: str | None,
        model: str | None,
        activity_type: str | None,
    ) -> dict:
        return {
            "from": from_,
            "to": to,
            "project": project_id,
            "application": application_id,
            "provider": provider,
            "model": model,
            "activity_type": activity_type,
        }
