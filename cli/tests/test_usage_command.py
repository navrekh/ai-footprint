"""SDK-contract tests for `aifootprint usage <subcommand>`."""

from __future__ import annotations

import json
import re

from aifootprint_cli.cli import main

PERIOD = {"from": "2026-01-01T00:00:00Z", "to": "2026-01-31T00:00:00Z"}
COUNTS = {
    "total": 100,
    "measured": 70,
    "partial": 25,
    "insufficient_data": 5,
    "coverage_percent": 70.0,
}
RANGE = {
    "status": "partial",
    "min": 10.0,
    "max": 20.0,
    "unit": "Wh",
    "total_workloads": 100,
    "measured_workloads": 70,
}


def test_usage_summary_hits_the_correct_endpoint(httpx_mock, api_env):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/summary.*"),
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )

    exit_code = main(["usage", "summary"])
    assert exit_code == 0


def test_usage_summary_never_averages_or_hides_coverage(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/summary.*"),
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )

    main(["usage", "summary"])
    captured = capsys.readouterr()

    assert "10–20 Wh" in captured.out
    assert "70 measured" in captured.out
    assert "25 partial" in captured.out
    assert "5 insufficient data" in captured.out


def test_usage_by_provider_renders_each_item(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/by-provider.*"),
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

    exit_code = main(["usage", "by-provider"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "openai" in captured.out


def test_usage_by_application_does_not_expose_an_application_filter(capsys):
    """The by-application breakdown IS the grouping - matching the
    backend contract that /v1/usage/by-application accepts no
    `application` query parameter at all.
    """
    exit_code = main(["usage", "by-application", "--application", "app_1"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "unrecognized arguments" in captured.err


def test_usage_timeseries_sends_granularity(httpx_mock, api_env):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/timeseries.*"),
        json={"period": PERIOD, "granularity": "week", "items": []},
    )

    main(["usage", "timeseries", "--granularity", "week"])

    request = httpx_mock.get_requests()[0]
    assert "granularity=week" in str(request.url)


def test_usage_json_output_is_valid_and_preserves_coverage(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/summary.*"),
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )

    main(["usage", "summary", "--output", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["workloads"]["coverage_percent"] == 70.0
    assert data["period"]["from"] == "2026-01-01T00:00:00Z"


def test_usage_filters_map_to_existing_query_parameters(httpx_mock, api_env):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/summary.*"),
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )

    main(
        [
            "usage",
            "summary",
            "--from",
            "2026-01-01T00:00:00",
            "--to",
            "2026-01-31T00:00:00",
            "--provider",
            "openai",
            "--model",
            "model-id",
            "--activity-type",
            "text_generation",
            "--project",
            "proj_1",
            "--application",
            "app_1",
        ]
    )

    request_url = str(httpx_mock.get_requests()[0].url)
    assert "provider=openai" in request_url
    assert "model=model-id" in request_url
    assert "activity_type=text_generation" in request_url
    assert "project=proj_1" in request_url
    assert "application=app_1" in request_url


def test_invalid_from_date_is_a_cli_usage_error(httpx_mock, api_env, capsys):
    """Regression test (P1): a malformed --from must not raise a raw
    ValueError that bypasses the centralized exit-code mapping.
    """
    exit_code = main(["usage", "summary", "--from", "not-a-date"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--from" in captured.err
    assert captured.out == ""


def test_invalid_to_date_is_a_cli_usage_error(httpx_mock, api_env, capsys):
    exit_code = main(["usage", "summary", "--to", "not-a-date"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--to" in captured.err
    assert captured.out == ""


def test_invalid_date_never_reaches_the_api(httpx_mock, api_env):
    """No response is registered - if a request were actually made,
    pytest-httpx would raise for an unmatched request instead of the
    test passing.
    """
    main(["usage", "summary", "--from", "not-a-date"])

    assert httpx_mock.get_requests() == []


def test_invalid_date_with_json_output_still_goes_to_stderr_only(httpx_mock, api_env, capsys):
    """--output json must not corrupt stdout with error text - stdout
    stays empty/clean, matching the JSON contract even on failure.
    """
    exit_code = main(["usage", "summary", "--from", "not-a-date", "--output", "json"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert captured.err != ""


def test_valid_iso8601_date_still_works(httpx_mock, api_env):
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"http://testserver/v1/usage/summary.*"),
        json={
            "period": PERIOD,
            "workloads": COUNTS,
            "energy": RANGE,
            "water": RANGE,
            "carbon": RANGE,
        },
    )

    exit_code = main(
        ["usage", "summary", "--from", "2026-01-01T00:00:00", "--to", "2026-01-31T00:00:00"]
    )

    assert exit_code == 0
    request_url = str(httpx_mock.get_requests()[0].url)
    assert "from=2026-01-01T00%3A00%3A00" in request_url
    assert "to=2026-01-31T00%3A00%3A00" in request_url
