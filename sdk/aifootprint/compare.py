"""Compare resource - maps to POST /v1/compare.

Every candidate is evaluated independently server-side; this SDK
returns `result.results` in exactly the order and shape the API
provided. It never sorts, scores, aggregates, or annotates a "winner" -
there is no ranking semantics anywhere in this module, by design (see
docs/ARCHITECTURE.md ADR-008).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._transport import Transport
from .models import CompareResult


class CompareResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        modality: str,
        activity_type: str,
        candidates: Sequence[Mapping[str, Any]],
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
    ) -> CompareResult:
        """`candidates` is 2 or more `{"provider": ..., "model": ...,
        "model_version": ...}` dicts (`model_version` optional). The
        server bounds the candidate count (`MAX_COMPARE_CANDIDATES`);
        exceeding it raises a ValidationError before any candidate runs.
        Does not accept `organization_id`/`project_id` - this call reads
        no tenant-owned data.
        """
        body = {
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
            "candidates": list(candidates),
        }
        data, request_id = self._transport.request("POST", "/v1/compare", json_body=body)
        result = CompareResult.model_validate(data)
        result.request_id = request_id
        return result
