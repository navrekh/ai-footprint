"""SDK-contract tests for `aifootprint benchmarks <subcommand>`."""

from __future__ import annotations

import json

from aifootprint_cli.cli import main


def test_list_hits_the_correct_endpoint(httpx_mock, api_env):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/benchmarks",
        json={"items": [], "total": 0},
    )
    exit_code = main(["benchmarks", "list"])
    assert exit_code == 0


def test_get_hits_the_correct_endpoint(httpx_mock, api_env):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/benchmarks/text_generation_standard",
        json={
            "benchmark_id": "text_generation_standard",
            "version": "1.0",
            "name": "Standard text generation",
            "description": "desc",
            "activity_type": "text_generation",
            "modality": "text",
            "parameters": {"input_tokens": 500},
        },
    )
    exit_code = main(["benchmarks", "get", "text_generation_standard"])
    assert exit_code == 0


def test_run_preserves_benchmark_version_and_candidate_order(httpx_mock, api_env, capsys):
    estimate = {
        "estimate_id": "est_1",
        "energy": {"status": "ok", "min": 1.0, "max": 2.0, "unit": "Wh"},
        "water": {"status": "ok", "min": 1.0, "max": 2.0, "unit": "mL"},
        "carbon": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "gCO2e"},
        "confidence": "medium",
        "evidence_level": 3,
        "accounting_boundary": "B",
        "methodology_version": "0.1",
        "assumptions": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/benchmarks/run",
        json={
            "benchmark_id": "text_generation_standard",
            "benchmark_version": "1.0",
            "modality": "text",
            "activity_type": "text_generation",
            "results": [
                {
                    "candidate": {"provider": "openai", "model": "a", "model_version": None},
                    "status": "success",
                    "resolved": None,
                    "estimate": estimate,
                    "normalized": None,
                    "error": None,
                },
                {
                    "candidate": {"provider": "openai", "model": "b", "model_version": None},
                    "status": "success",
                    "resolved": None,
                    "estimate": estimate,
                    "normalized": None,
                    "error": None,
                },
            ],
        },
    )

    exit_code = main(
        [
            "benchmarks",
            "run",
            "text_generation_standard",
            "--candidate",
            "openai:a",
            "--candidate",
            "openai:b",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "1.0" in captured.out
    assert captured.out.index("openai/a") < captured.out.index("openai/b")

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["benchmark_id"] == "text_generation_standard"
    assert body["candidates"] == [
        {"provider": "openai", "model": "a"},
        {"provider": "openai", "model": "b"},
    ]


def test_run_never_shows_ranking_vocabulary(httpx_mock, api_env, capsys):
    estimate = {
        "estimate_id": "est_1",
        "energy": {"status": "ok", "min": 1.0, "max": 2.0, "unit": "Wh"},
        "water": {"status": "ok", "min": 1.0, "max": 2.0, "unit": "mL"},
        "carbon": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "gCO2e"},
        "confidence": "medium",
        "evidence_level": 3,
        "accounting_boundary": "B",
        "methodology_version": "0.1",
        "assumptions": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/benchmarks/run",
        json={
            "benchmark_id": "b1",
            "benchmark_version": "1.0",
            "modality": "text",
            "activity_type": "text_generation",
            "results": [
                {
                    "candidate": {"provider": "openai", "model": "a", "model_version": None},
                    "status": "success",
                    "resolved": None,
                    "estimate": estimate,
                    "normalized": None,
                    "error": None,
                }
            ],
        },
    )

    main(["benchmarks", "run", "b1", "--candidate", "openai:a", "--candidate", "openai:b"])
    captured = capsys.readouterr()

    lowered = captured.out.lower()
    for word in ("winner", "best", "score", "rank"):
        assert word not in lowered


def test_run_requires_candidates():
    exit_code = main(["benchmarks", "run", "b1"])
    assert exit_code == 2
