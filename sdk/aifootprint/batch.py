"""Batch resource - maps to POST /v1/batch-estimate: a bounded, stateless
batch of independent estimates. A single invalid workload never fails
the whole batch - each item's outcome is reported independently in
`result.results`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._transport import Transport
from .models import BatchResult


class BatchResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(self, workloads: Sequence[Mapping[str, Any]]) -> BatchResult:
        """`workloads` is a sequence of plain dicts, each shaped like the
        keyword arguments to `client.estimates.create()` (provider,
        model, modality, activity_type, and the same optional
        quantity fields). The server enforces a maximum batch size
        (`MAX_BATCH_SIZE`) and rejects an oversized batch as a
        ValidationError before evaluating any item.
        """
        data, request_id = self._transport.request(
            "POST",
            "/v1/batch-estimate",
            json_body={"workloads": list(workloads)},
        )
        result = BatchResult.model_validate(data)
        result.request_id = request_id
        return result
