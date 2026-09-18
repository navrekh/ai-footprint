"""End-to-end integration tests: real SDK, real HTTP, real local backend,
real Postgres. See tests/integration/conftest.py and
tests/integration/README.md for what's required to run these.

Marked `integration` so the default `pytest` run (unit tests only, no
external process required) skips this file entirely.
"""

from __future__ import annotations

import uuid

import pytest

from aifootprint import AIClient, NotFoundError

pytestmark = pytest.mark.integration


def test_health(live_backend_url):
    with AIClient(base_url=live_backend_url) as anon_client:
        assert anon_client.health() == {"status": "ok"}


def test_bootstrap_returns_a_working_api_key(bootstrapped_org):
    assert bootstrapped_org.api_key.key.startswith("afp_test_")
    assert bootstrapped_org.organization.name.startswith("SDK Integration Test Org")
    assert bootstrapped_org.request_id is not None


def test_providers_and_models_registries_are_seeded(client):
    providers = client.providers.list()
    assert any(p.id == "openai" for p in providers)

    models = client.models.list(provider="openai")
    assert any(m.name == "test-only-demo-model" for m in models)


def test_estimate_is_stateless_and_preserves_ranges(client):
    estimate = client.estimates.create(
        provider="openai",
        model="test-only-demo-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=1000,
        output_tokens=500,
    )
    assert estimate.energy.status == "ok"
    assert estimate.energy.min < estimate.energy.max
    assert estimate.methodology_version == "TEST_ONLY-0.1"
    assert estimate.request_id is not None


def test_event_is_persisted_and_readable_via_workloads(client):
    event = client.events.create(
        provider="openai",
        model="test-only-demo-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=2000,
        output_tokens=1000,
    )
    assert event.status in ("measured", "partial", "insufficient_data")

    workload = client.workloads.get(event.workload_id)
    assert workload.provider == "openai"
    assert workload.input_tokens == 2000

    persisted = client.estimates.get(event.estimate_id)
    assert persisted.workload_id == event.workload_id


def test_idempotency_key_replays_the_same_event_on_a_real_server(client):
    key = f"integration-test-{uuid.uuid4()}"
    first = client.events.create(
        provider="openai",
        model="test-only-demo-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=100,
        idempotency_key=key,
    )
    second = client.events.create(
        provider="openai",
        model="test-only-demo-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=100,
        idempotency_key=key,
    )
    assert first.idempotent_replay is False
    assert second.idempotent_replay is True
    assert second.event_id == first.event_id
    assert second.estimate_id == first.estimate_id


def test_usage_summary_reflects_recorded_events(client):
    client.events.create(
        provider="openai",
        model="test-only-demo-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=500,
    )
    summary = client.usage.summary()
    assert summary.workloads.total >= 1
    assert summary.request_id is not None


def test_not_found_error_carries_status_and_request_id(client):
    with pytest.raises(NotFoundError) as exc_info:
        client.projects.get("proj_does_not_exist")
    error = exc_info.value
    assert error.status_code == 404
    assert error.request_id is not None


def test_authentication_error_on_invalid_api_key(live_backend_url):
    with AIClient(api_key="afp_test_definitely_invalid", base_url=live_backend_url) as bad_client:
        from aifootprint import AuthenticationError

        with pytest.raises(AuthenticationError):
            bad_client.projects.list()


def test_compare_reports_independent_results_without_ranking(client):
    result = client.compare.create(
        modality="text",
        activity_type="text_generation",
        input_tokens=1000,
        candidates=[
            {"provider": "openai", "model": "test-only-demo-model"},
            {"provider": "openai", "model": "some-nonexistent-model"},
        ],
    )
    assert len(result.results) == 2
    statuses = {item.candidate.model: item.status for item in result.results}
    assert statuses["test-only-demo-model"] == "success"
    assert statuses["some-nonexistent-model"] == "failed"
