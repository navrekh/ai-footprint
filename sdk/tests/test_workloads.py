from aifootprint.models import Workload, WorkloadPage


def _workload_body(**overrides) -> dict:
    body = {
        "id": "evt_1",
        "organization_id": "org_1",
        "project_id": "proj_1",
        "application_id": None,
        "provider": "openai",
        "model": "model-id",
        "model_version": None,
        "modality": "text",
        "activity_type": "text_generation",
        "timestamp": "2026-01-01T00:00:00Z",
        "input_tokens": 100,
        "output_tokens": 50,
        "input_characters": None,
        "output_characters": None,
        "image_count": None,
        "image_width": None,
        "image_height": None,
        "video_seconds": None,
        "video_resolution": None,
        "audio_seconds": None,
        "tool_calls": None,
        "duration_seconds": None,
        "duration_ms": None,
        "parent_workload_id": None,
        "metadata": None,
        "created_at": "2026-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def test_list_is_cursor_paginated_not_limit_offset(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/workloads?limit=20",
        json={"items": [_workload_body()], "next_cursor": "opaque-cursor-value"},
    )
    result = client.workloads.list()
    assert isinstance(result, WorkloadPage)
    assert result.next_cursor == "opaque-cursor-value"
    assert isinstance(result.items[0], Workload)


def test_list_passes_cursor_through_on_next_page(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/workloads?cursor=opaque-cursor-value&limit=20",
        json={"items": [], "next_cursor": None},
    )
    result = client.workloads.list(cursor="opaque-cursor-value")
    assert result.next_cursor is None
    assert result.items == []


def test_get(httpx_mock, client):
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/workloads/evt_1", json=_workload_body()
    )
    result = client.workloads.get("evt_1")
    assert result.id == "evt_1"


def test_metadata_field_is_preserved(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/workloads/evt_1",
        json=_workload_body(metadata={"customer_tier": "enterprise"}),
    )
    result = client.workloads.get("evt_1")
    assert result.metadata == {"customer_tier": "enterprise"}
