"""Benchmarks resource - maps to GET /v1/benchmarks, GET
/v1/benchmarks/{id}, and POST /v1/benchmarks/run.

`list()`/`get()` are public - no API key required, matching
`GET /v1/providers`/`/v1/models`/`/v1/methodology`. `run()` requires a
valid API key but reads no tenant-owned data, exactly like
`client.compare.create()`. Benchmark definitions are static and
versioned server-side; running one never ranks, scores, or picks a
winner among candidates - see compare.py.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._transport import Transport
from .models import BenchmarkDefinition, BenchmarkList, BenchmarkRunResult


class BenchmarksResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(
        self, *, activity_type: str | None = None, modality: str | None = None
    ) -> BenchmarkList:
        data, request_id = self._transport.request(
            "GET",
            "/v1/benchmarks",
            params={"activity_type": activity_type, "modality": modality},
        )
        result = BenchmarkList.model_validate(data)
        result.request_id = request_id
        return result

    def get(self, benchmark_id: str) -> BenchmarkDefinition:
        data, request_id = self._transport.request("GET", f"/v1/benchmarks/{benchmark_id}")
        result = BenchmarkDefinition.model_validate(data)
        result.request_id = request_id
        return result

    def run(
        self, benchmark_id: str, candidates: Sequence[Mapping[str, Any]]
    ) -> BenchmarkRunResult:
        """`candidates` is 2 or more `{"provider": ..., "model": ...,
        "model_version": ...}` dicts, same shape as `client.compare.create()`.
        """
        data, request_id = self._transport.request(
            "POST",
            "/v1/benchmarks/run",
            json_body={"benchmark_id": benchmark_id, "candidates": list(candidates)},
        )
        result = BenchmarkRunResult.model_validate(data)
        result.request_id = request_id
        return result
