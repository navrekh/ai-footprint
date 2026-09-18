from datetime import datetime, timezone

from aifootprint.models import (
    UsageByActivityResult,
    UsageByApplicationResult,
    UsageByModelResult,
    UsageByProviderResult,
    UsageSummary,
    UsageTimeseriesResult,
)

PERIOD = {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z"}
COUNTS = {
    "total": 100,
    "measured": 70,
    "partial": 25,
    "insufficient_data": 5,
    "coverage_percent": 70.0,
}
RANGE = {
    "status": "partial",
    "min": 1.0,
    "max": 2.0,
    "unit": "Wh",
    "total_workloads": 100,
    "measured_workloads": 70,
}


def test_summary_default_no_filters(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/summary",
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )
    result = client.usage.summary()
    assert isinstance(result, UsageSummary)
    assert result.workloads.total == 100
    assert result.workloads.coverage_percent == 70.0
    # Coverage is never rounded up to imply completeness.
    assert (
        result.workloads.measured + result.workloads.partial + result.workloads.insufficient_data
        == 100
    )


def test_summary_with_date_and_dimension_filters(httpx_mock, client):
    from_ = datetime(2026, 1, 1, tzinfo=timezone.utc)
    to = datetime(2026, 1, 31, tzinfo=timezone.utc)
    httpx_mock.add_response(
        method="GET",
        url=(
            "http://testserver/v1/usage/summary"
            "?from=2026-01-01T00%3A00%3A00%2B00%3A00&to=2026-01-31T00%3A00%3A00%2B00%3A00"
            "&project=proj_1&application=app_1&provider=openai&model=model-id"
            "&activity_type=text_generation"
        ),
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )
    result = client.usage.summary(
        from_=from_,
        to=to,
        project_id="proj_1",
        application_id="app_1",
        provider="openai",
        model="model-id",
        activity_type="text_generation",
    )
    assert result.workloads.total == 100


def test_by_provider_pagination(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/by-provider?limit=10&offset=5",
        json={
            "period": PERIOD,
            "items": [
                {
                    "provider": "openai",
                    "workloads": COUNTS,
                    "energy": RANGE,
                    "water": RANGE,
                    "carbon": RANGE,
                }
            ],
            "total": 1,
        },
    )
    result = client.usage.by_provider(limit=10, offset=5)
    assert isinstance(result, UsageByProviderResult)
    assert result.items[0].provider == "openai"


def test_by_model(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/by-model?limit=50&offset=0",
        json={
            "period": PERIOD,
            "items": [
                {
                    "provider": "openai",
                    "model": "model-id",
                    "model_version": "v2",
                    "workloads": COUNTS,
                    "energy": RANGE,
                    "water": RANGE,
                    "carbon": RANGE,
                }
            ],
            "total": 1,
        },
    )
    result = client.usage.by_model()
    assert isinstance(result, UsageByModelResult)
    assert result.items[0].model_version == "v2"


def test_by_activity(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/by-activity?limit=50&offset=0",
        json={
            "period": PERIOD,
            "items": [
                {
                    "activity_type": "text_generation",
                    "workloads": COUNTS,
                    "energy": RANGE,
                    "water": RANGE,
                    "carbon": RANGE,
                }
            ],
            "total": 1,
        },
    )
    result = client.usage.by_activity()
    assert isinstance(result, UsageByActivityResult)


def test_by_application_does_not_send_an_application_filter(httpx_mock, client):
    """Matches the actual backend contract: GET /v1/usage/by-application
    does not accept an `application` query parameter at all (unlike the
    other five usage endpoints) - verified against
    app/api/routes/usage.py, not assumed.
    """
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/by-application?project=proj_1&limit=50&offset=0",
        json={
            "period": PERIOD,
            "items": [
                {
                    "application_id": "app_1",
                    "application_name": "Support Bot",
                    "project_id": "proj_1",
                    "workloads": COUNTS,
                    "energy": RANGE,
                    "water": RANGE,
                    "carbon": RANGE,
                }
            ],
            "total": 1,
        },
    )
    result = client.usage.by_application(project_id="proj_1")

    request = httpx_mock.get_requests()[0]
    assert "application=" not in str(request.url)
    assert isinstance(result, UsageByApplicationResult)
    assert result.items[0].application_id == "app_1"


def test_timeseries_default_granularity(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/timeseries?granularity=day",
        json={
            "period": PERIOD,
            "granularity": "day",
            "items": [
                {
                    "period_start": "2026-01-01T00:00:00Z",
                    "workloads": COUNTS,
                    "energy": RANGE,
                    "water": RANGE,
                    "carbon": RANGE,
                }
            ],
        },
    )
    result = client.usage.timeseries()
    assert isinstance(result, UsageTimeseriesResult)
    assert result.granularity == "day"


def test_timeseries_explicit_granularity(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/timeseries?granularity=month",
        json={"period": PERIOD, "granularity": "month", "items": []},
    )
    result = client.usage.timeseries(granularity="month")
    assert result.granularity == "month"
    assert result.items == []
