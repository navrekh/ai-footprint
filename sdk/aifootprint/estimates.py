"""Estimates resource.

`create()` maps to POST /v1/estimate: a stateless calculation with no
persistence - nothing is written to the database, and no estimate_id
returned here can later be looked up via `get()`. `get()` maps to
GET /v1/estimates/{id}, which only finds estimates created via
`client.events.create()`.
"""

from __future__ import annotations

from ._transport import Transport
from .models import ClientContext, Estimate, PersistedEstimate


def _serialize_client(client: ClientContext | dict | None) -> dict | None:
    """Accepts either a typed `ClientContext` or a plain dict (mirroring
    how `metadata` already accepts a plain dict), so callers are never
    forced to import `ClientContext` for a simple case.
    """
    if client is None:
        return None
    if isinstance(client, ClientContext):
        return client.model_dump(mode="json", exclude_none=True)
    return client


def build_workload_body(
    *,
    provider: str,
    model: str,
    modality: str,
    activity_type: str,
    model_version: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    input_characters: int | None = None,
    output_characters: int | None = None,
    image_count: int | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
    video_seconds: float | None = None,
    video_resolution: str | None = None,
    audio_seconds: float | None = None,
    tool_calls: int | None = None,
    duration_seconds: float | None = None,
    duration_ms: float | None = None,
    metadata: dict | None = None,
    client: ClientContext | dict | None = None,
) -> dict:
    """Shared field set across /v1/estimate, /v1/events, and each item
    of /v1/batch-estimate - mirrors WorkloadInput exactly (see
    backend/footprint-api/app/schemas/workload.py). Kept as a plain
    function (not a shared base class) so each resource module's public
    method signature stays explicit and self-documenting.

    `client` is optional, observational client/integration metadata
    (Sprint 6) - it never affects the resulting estimate.
    """
    return {
        "provider": provider,
        "model": model,
        "model_version": model_version,
        "modality": modality,
        "activity_type": activity_type,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_characters": input_characters,
        "output_characters": output_characters,
        "image_count": image_count,
        "image_width": image_width,
        "image_height": image_height,
        "video_seconds": video_seconds,
        "video_resolution": video_resolution,
        "audio_seconds": audio_seconds,
        "tool_calls": tool_calls,
        "duration_seconds": duration_seconds,
        "duration_ms": duration_ms,
        "metadata": metadata,
        "client": _serialize_client(client),
    }


class EstimatesResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        provider: str,
        model: str,
        modality: str,
        activity_type: str,
        model_version: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        input_characters: int | None = None,
        output_characters: int | None = None,
        image_count: int | None = None,
        image_width: int | None = None,
        image_height: int | None = None,
        video_seconds: float | None = None,
        video_resolution: str | None = None,
        audio_seconds: float | None = None,
        tool_calls: int | None = None,
        duration_seconds: float | None = None,
        duration_ms: float | None = None,
        metadata: dict | None = None,
        client: ClientContext | dict | None = None,
    ) -> Estimate:
        body = build_workload_body(
            provider=provider,
            model=model,
            modality=modality,
            activity_type=activity_type,
            model_version=model_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_characters=input_characters,
            output_characters=output_characters,
            image_count=image_count,
            image_width=image_width,
            image_height=image_height,
            video_seconds=video_seconds,
            video_resolution=video_resolution,
            audio_seconds=audio_seconds,
            tool_calls=tool_calls,
            duration_seconds=duration_seconds,
            duration_ms=duration_ms,
            metadata=metadata,
            client=client,
        )
        data, request_id = self._transport.request("POST", "/v1/estimate", json_body=body)
        result = Estimate.model_validate(data)
        result.request_id = request_id
        return result

    def get(self, estimate_id: str) -> PersistedEstimate:
        """Only estimates created via `client.events.create()` are
        persisted and retrievable here.
        """
        data, request_id = self._transport.request("GET", f"/v1/estimates/{estimate_id}")
        result = PersistedEstimate.model_validate(data)
        result.request_id = request_id
        return result
