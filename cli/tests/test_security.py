"""Sprint 7 FRD section 39.17's hard security boundary: the API key
must never appear in stdout, stderr, tracebacks, exceptions, URLs, or
JSON output during normal operation - across every failure mode the
CLI can produce.
"""

from __future__ import annotations

from aifootprint_cli.cli import main

SECRET_KEY = "afp_live_super-secret-value-should-never-leak"


def test_key_never_appears_in_a_successful_json_response(httpx_mock, monkeypatch, capsys):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", SECRET_KEY)
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://testserver")
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/benchmarks",
        json={"items": [], "total": 0},
    )

    main(["benchmarks", "list", "--output", "json"])
    captured = capsys.readouterr()

    assert SECRET_KEY not in captured.out
    assert SECRET_KEY not in captured.err


def test_key_never_appears_on_an_authentication_failure(httpx_mock, monkeypatch, capsys):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", SECRET_KEY)
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://testserver")
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/usage/summary",
        status_code=401,
        json={
            "error": {"code": "INVALID_API_KEY", "message": "Invalid key.", "request_id": "req_1"}
        },
    )

    exit_code = main(["usage", "summary"])
    captured = capsys.readouterr()

    assert exit_code == 3
    assert SECRET_KEY not in captured.out
    assert SECRET_KEY not in captured.err


def test_key_never_appears_in_a_transport_error_message(monkeypatch, capsys):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", SECRET_KEY)
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://127.0.0.1:1")

    exit_code = main(["usage", "summary"])
    captured = capsys.readouterr()

    assert exit_code == 9
    assert SECRET_KEY not in captured.out
    assert SECRET_KEY not in captured.err


def test_key_never_appears_in_the_request_url(httpx_mock, monkeypatch):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", SECRET_KEY)
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://testserver")
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/benchmarks", json={"items": [], "total": 0}
    )

    main(["benchmarks", "list"])

    for request in httpx_mock.get_requests():
        assert SECRET_KEY not in str(request.url)


def test_key_is_sent_only_as_the_authorization_header(httpx_mock, monkeypatch):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", SECRET_KEY)
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://testserver")
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/benchmarks", json={"items": [], "total": 0}
    )

    main(["benchmarks", "list"])

    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == f"Bearer {SECRET_KEY}"


def test_explicit_cli_api_key_option_never_leaks_into_output(httpx_mock, capsys):
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/benchmarks", json={"items": [], "total": 0}
    )

    main(["benchmarks", "list", "--api-key", SECRET_KEY, "--base-url", "http://testserver"])
    captured = capsys.readouterr()

    assert SECRET_KEY not in captured.out
    assert SECRET_KEY not in captured.err


def test_key_never_appears_in_a_configuration_error_message(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config" / "aifootprint"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(f'{{"api_key": "{SECRET_KEY}", not valid json')
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    exit_code = main(["benchmarks", "list"])
    captured = capsys.readouterr()

    assert exit_code == 10
    assert SECRET_KEY not in captured.out
    assert SECRET_KEY not in captured.err


def test_key_never_appears_in_an_unhandled_exception_traceback(httpx_mock, monkeypatch, capsys):
    """Even a genuinely unexpected error (simulated via a malformed
    response body the SDK cannot parse) must not echo the key anywhere
    in the printed error text.
    """
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", SECRET_KEY)
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://testserver")
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/benchmarks",
        status_code=200,
        content=b"not json",
    )

    exit_code = main(["benchmarks", "list"])
    captured = capsys.readouterr()

    assert exit_code == 8  # APIError raised for a non-JSON success response
    assert SECRET_KEY not in captured.out
    assert SECRET_KEY not in captured.err
