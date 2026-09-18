"""Shared rendering for `ComparisonResultItem` lists - used by both
`compare` and `benchmarks run`, exactly like the developer console
shares one `ComparisonResultCard` component between the two (Sprint 5D)
so this "no ranking" guarantee cannot silently diverge between them.
"""

from __future__ import annotations

from collections.abc import Sequence

from aifootprint.models import ComparisonResultItem

from ..output import format_enum, format_range


def render_comparison_results(results: Sequence[ComparisonResultItem]) -> None:
    for index, result in enumerate(results):
        identity = result.resolved or result.candidate
        label = f"{identity.provider}/{identity.model}"
        if identity.model_version:
            label += f"@{identity.model_version}"
        print(f"[{index}] {label} - {result.status}")
        if result.status == "success" and result.estimate is not None:
            estimate = result.estimate
            print(f"      Energy: {format_range(estimate.energy)}")
            print(f"      Water: {format_range(estimate.water)}")
            print(f"      Carbon: {format_range(estimate.carbon)}")
            confidence = (
                format_enum(estimate.confidence) if estimate.confidence else "Insufficient data"
            )
            print(f"      Confidence: {confidence}")
            if result.normalized is not None:
                denom = result.normalized.denominator
                print(f"      Normalized per {denom.value:g} {denom.unit}:")
                for metric_label, metric in (
                    ("Energy", result.normalized.energy),
                    ("Water", result.normalized.water),
                    ("Carbon", result.normalized.carbon),
                ):
                    if metric is not None:
                        print(f"        {metric_label}: {format_range(metric)}")
        elif result.error is not None:
            print(f"      Error: {result.error.message} ({result.error.code})")
