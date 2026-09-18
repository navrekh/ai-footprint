"""SDK-contract tests for `aifootprint compare` - explicitly verifying
no ranking/scoring/winner semantics ever leak into CLI output.
"""

from __future__ import annotations

import json

from aifootprint_cli.cli import main

BASE = [
    "compare",
    "--modality",
    "text",
    "--activity-type",
    "text_generation",
    "--candidate",
    "openai:model-a",
    "--candidate",
    "anthropic:model-b",
]

ESTIMATE = {
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


def _compare_response() -> dict:
    return {
        "comparison_id": "cmp_1",
        "modality": "text",
        "activity_type": "text_generation",
        "results": [
            {
                "candidate": {"provider": "openai", "model": "model-a", "model_version": None},
                "status": "success",
                "resolved": {"provider": "openai", "model": "model-a", "model_version": "v1"},
                "estimate": ESTIMATE,
                "normalized": None,
                "error": None,
            },
            {
                "candidate": {"provider": "anthropic", "model": "model-b", "model_version": None},
                "status": "success",
                "resolved": {"provider": "anthropic", "model": "model-b", "model_version": "v2"},
                "estimate": ESTIMATE,
                "normalized": None,
                "error": None,
            },
        ],
    }


def test_compare_hits_the_correct_endpoint_with_both_candidates(httpx_mock, api_env):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )

    exit_code = main(BASE)

    assert exit_code == 0
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["candidates"] == [
        {"provider": "openai", "model": "model-a"},
        {"provider": "anthropic", "model": "model-b"},
    ]


def test_candidate_order_is_preserved_exactly_as_returned(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )

    main(BASE)
    captured = capsys.readouterr()

    first_index = captured.out.index("openai/model-a")
    second_index = captured.out.index("anthropic/model-b")
    assert first_index < second_index


def test_output_never_contains_ranking_or_winner_vocabulary(httpx_mock, api_env, capsys):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/compare", json=_compare_response()
    )

    main(BASE)
    captured = capsys.readouterr()

    forbidden = ["winner", "best", "recommended", "score", "rank", "#1"]
    lowered = captured.out.lower()
    for word in forbidden:
        assert word not in lowered


def test_a_failed_candidate_is_shown_not_hidden(httpx_mock, api_env, capsys):
    response = _compare_response()
    response["results"][1] = {
        "candidate": {"provider": "anthropic", "model": "model-b", "model_version": None},
        "status": "failed",
        "resolved": None,
        "estimate": None,
        "normalized": None,
        "error": {"code": "MODEL_NOT_FOUND", "message": "Model not found.", "request_id": "req_z"},
    }
    httpx_mock.add_response(method="POST", url="http://testserver/v1/compare", json=response)

    main(BASE)
    captured = capsys.readouterr()

    assert "Model not found." in captured.out
    assert "anthropic/model-b" in captured.out


def test_zero_candidates_is_a_validation_error():
    exit_code = main(["compare", "--modality", "text", "--activity-type", "text_generation"])
    assert exit_code == 2


def test_one_candidate_is_a_cli_usage_error(httpx_mock, capsys):
    """P1 regression: `action='append', required=True` alone only
    enforces >=1 candidate, not the required >=2 - the minimum count
    must be enforced by parse_candidates() itself.
    """
    exit_code = main(
        [
            "compare",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--candidate",
            "openai:model-a",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "at least 2" in captured.err


def test_one_candidate_makes_no_http_request(httpx_mock):
    """No response is registered - if a request were actually made,
    pytest-httpx would raise for an unmatched request instead of the
    test passing.
    """
    main(
        [
            "compare",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--candidate",
            "openai:model-a",
        ]
    )

    assert httpx_mock.get_requests() == []


def test_malformed_candidate_is_a_cli_usage_error(capsys):
    exit_code = main(
        [
            "compare",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--candidate",
            "not-valid",
            "--candidate",
            "openai:model-a",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Invalid --candidate" in captured.err


def test_two_malformed_candidates_is_still_a_cli_usage_error_not_a_count_error(capsys):
    """Exactly 2 candidates supplied, but one is malformed - the count
    check must not mask a genuine format error.
    """
    exit_code = main(
        [
            "compare",
            "--modality",
            "text",
            "--activity-type",
            "text_generation",
            "--candidate",
            "not-valid",
            "--candidate",
            "also-not-valid",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Invalid --candidate" in captured.err
