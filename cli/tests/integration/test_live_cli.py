"""End-to-end tests: the real `aifootprint` CLI, in process, against a
real running backend (Sprint 7 FRD section 39.18's Integration/E2E
requirements). See conftest.py/README.md for the fixtures and scope.
"""

from __future__ import annotations

import json

import pytest

from aifootprint_cli.cli import main

pytestmark = pytest.mark.integration


def test_event_success(cli_env, capsys):
    exit_code = main(
        [
            "event",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--input-tokens",
            "2000",
            "--output-tokens",
            "1000",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Workload ID:" in captured.out
    assert "Estimate ID:" in captured.out


def test_estimate_success(cli_env, capsys):
    exit_code = main(
        [
            "estimate",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--input-tokens",
            "2000",
            "--output-tokens",
            "1000",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Energy:" in captured.out
    assert "–" in captured.out  # a real range, not a collapsed point value


def test_usage_summary_success(cli_env, capsys):
    main(
        [
            "event",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--input-tokens",
            "100",
            "--output-tokens",
            "50",
        ]
    )
    capsys.readouterr()

    exit_code = main(["usage", "summary"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "total" in captured.out


def test_compare_success(cli_env, capsys):
    exit_code = main(
        [
            "compare",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--input-tokens",
            "2000",
            "--output-tokens",
            "1000",
            "--candidate",
            "openai:test-only-demo-model",
            "--candidate",
            "openai:test-only-demo-model",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Comparison ID:" in captured.out
    assert "[0]" in captured.out
    assert "[1]" in captured.out


def test_benchmark_success(cli_env, capsys):
    list_exit = main(["benchmarks", "list"])
    capsys.readouterr()
    assert list_exit == 0

    run_exit = main(
        [
            "benchmarks",
            "run",
            "text_generation_standard",
            "--candidate",
            "openai:test-only-demo-model",
            "--candidate",
            "openai:test-only-demo-model",
        ]
    )
    captured = capsys.readouterr()

    assert run_exit == 0
    assert "text_generation_standard" in captured.out


def test_authentication_failure(cli_env, capsys):
    exit_code = main(["usage", "summary", "--api-key", "afp_live_totally_bogus_key"])
    captured = capsys.readouterr()

    assert exit_code == 3
    assert "afp_live_totally_bogus_key" not in captured.out
    assert "afp_live_totally_bogus_key" not in captured.err


def test_authorization_failure_cross_project(cli_env, capsys):
    from aifootprint import AIClient

    with AIClient(api_key=cli_env["api_key"], base_url=cli_env["base_url"]) as client:
        other_project = client.projects.create(name="Other CLI Integration Project")
        scoped_key = client.api_keys.create(
            name="scoped-key", project_id=cli_env["project_id"]
        )

    exit_code = main(
        [
            "event",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--project",
            other_project.id,
            "--api-key",
            scoped_key.key,
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 4
    assert scoped_key.key not in captured.out
    assert scoped_key.key not in captured.err


def test_validation_failure_incompatible_modality(cli_env, capsys):
    exit_code = main(
        [
            "estimate",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "image",
            "--activity-type",
            "text_generation",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error:" in captured.err


def test_transport_failure_unreachable_host(monkeypatch, capsys):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", "afp_live_irrelevant")
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", "http://127.0.0.1:1")

    exit_code = main(["usage", "summary"])
    captured = capsys.readouterr()

    assert exit_code == 9
    assert "afp_live_irrelevant" not in captured.out
    assert "afp_live_irrelevant" not in captured.err


def test_json_output_is_valid_and_scriptable(cli_env, capsys):
    exit_code = main(
        [
            "estimate",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--input-tokens",
            "2000",
            "--output-tokens",
            "1000",
            "--output",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    data = json.loads(captured.out)  # raises if stdout is not clean, valid JSON
    assert "energy" in data
    assert "request_id" in data
    assert "\x1b[" not in captured.out


def test_non_interactive_execution_uses_only_environment_variables(cli_env, capsys):
    """No --api-key/--base-url flag, no local config file - exactly the
    documented CI/CD invocation shape.
    """
    exit_code = main(
        [
            "estimate",
            "--provider",
            "openai",
            "--model",
            "test-only-demo-model",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--output",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    json.loads(captured.out)
