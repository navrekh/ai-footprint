"""Output formatting - the CLI's one place that turns an SDK result
model into terminal text or JSON (Sprint 7 FRD section 39.10).

Hard invariants enforced here, mirroring the developer console's
MetricRangeDisplay (frontend/developer-console/src/components/resource/
MetricRangeDisplay.tsx):

* a range's min/max are never averaged or collapsed into one number;
* `insufficient_data` is always shown as the literal text
  "Insufficient data", never as 0 or blank;
* nothing here sorts, scores, ranks, or labels a candidate a winner -
  every result list is rendered in exactly the order the API returned.

JSON output is always the SDK's own response shape via
`model_dump(mode="json")`, plus the out-of-band `request_id` (excluded
from `model_dump()` by `ResultBase` itself - see sdk/aifootprint/
models.py) merged back in - never a hand-built dict that could drift
from the real API contract.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from aifootprint.models import ResultBase


def to_json_dict(result: ResultBase) -> dict[str, Any]:
    """`by_alias=True` matters for one field: `UsagePeriod.from_` (Python
    can't name an attribute `from`) must render as `"from"` in JSON
    output, matching the real API field name - not the Python-only
    attribute name `"from_"`.
    """
    data = result.model_dump(mode="json", by_alias=True)
    data["request_id"] = result.request_id
    return data


def print_json(result: ResultBase) -> None:
    print(json.dumps(to_json_dict(result), indent=2))


def format_range(range_obj: Any) -> str:
    """`range_obj` is any MetricRange/AggregateMetricRange/
    NormalizedMetricRange - anything with `.status`/`.min`/`.max`/
    `.unit`. `None` (e.g. an absent optional normalized metric) also
    renders as "Insufficient data" rather than being a caller's special
    case to handle.
    """
    if range_obj is None:
        return "Insufficient data"
    if range_obj.status == "insufficient_data" or range_obj.min is None or range_obj.max is None:
        return "Insufficient data"
    return f"{_trim(range_obj.min)}–{_trim(range_obj.max)} {range_obj.unit}"


def _trim(value: float) -> str:
    """Renders 10.0 as "10" and 10.5 as "10.5" - avoids a wall of
    trailing .0s in table output without rounding away real precision.
    """
    text = f"{value:.6g}"
    return text


def format_enum(value: Any) -> str:
    """Renders a `str, Enum` member (e.g. `Confidence.LOW`) as its plain
    wire value ("low") rather than Python's default `repr`-ish
    `str(member)` ("Confidence.LOW") - the value is exactly what the
    API itself sent, so that's what a human-readable render should show.
    """
    return value.value if isinstance(value, Enum) else str(value)


def format_workload_counts(counts: Any) -> str:
    return (
        f"{counts.total} total · {counts.measured} measured · "
        f"{counts.partial} partial · {counts.insufficient_data} insufficient data "
        f"({counts.coverage_percent:.1f}% coverage)"
    )


def format_request_id(result: ResultBase) -> str | None:
    return f"Request ID: {result.request_id}" if result.request_id else None


def print_kv(label: str, value: str) -> None:
    print(f"{label}: {value}")


def print_request_id(result: ResultBase) -> None:
    line = format_request_id(result)
    if line:
        print(line)
