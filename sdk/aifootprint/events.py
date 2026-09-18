"""Events resource - maps to POST /v1/events: persists an AIWorkload and
creates its Estimate.

Idempotency (see backend/footprint-api/app/schemas/workload.py and
README "Idempotency" section): `idempotency_key` is a **request BODY
field**, not an HTTP header - verified directly against the backend
schema, not assumed. Resubmitting the same key for the same project
returns the original result with `idempotent_replay=True` instead of
creating a duplicate measurement, enforced by a database unique
constraint server-side. This SDK never generates an idempotency key on
a caller's behalf - if retry-safety matters, pass a stable key you
control (e.g. your own request/job id).
"""

from __future__ import annotations

from datetime import datetime

from ._transport import Transport
from .estimates import build_workload_body
from .models import ClientContext, Event


class EventsResource:
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
        project_id: str | None = None,
        application_id: str | None = None,
        idempotency_key: str | None = None,
        timestamp: datetime | None = None,
        parent_workload_id: str | None = None,
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
    ) -> Event:
        """`project_id` is required for an organization-level API key
        and optional (must match the key's own project) for a
        project-scoped key. `application_id`, when given, must belong to
        the same project the event is persisted under.

        `client` is optional client/integration metadata (Sprint 6)
        identifying the software surface instrumenting this event -
        distinct from `application_id`. It is purely observational and
        never affects the resulting estimate.
        """
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
        body.update(
            {
                "project_id": project_id,
                "application_id": application_id,
                "idempotency_key": idempotency_key,
                "timestamp": timestamp,
                "parent_workload_id": parent_workload_id,
            }
        )
        data, request_id = self._transport.request("POST", "/v1/events", json_body=body)
        result = Event.model_validate(data)
        result.request_id = request_id
        return result
