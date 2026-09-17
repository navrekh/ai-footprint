"""Normalized resource-intensity arithmetic (docs/METHODOLOGY.md section 25,
docs/ARCHITECTURE.md ADR-010).

Normalization is presentation-layer arithmetic over an already-computed,
approved estimate. It never calls the estimation pipeline differently,
never changes a stored coefficient, and never invents a denominator for a
workload type that has none of the relevant quantity fields populated.

Denominator.value is always expressed already in the unit a caller can
read directly: e.g. 1.5 "1K tokens" for a 1,500-token workload, so that
`raw_range / denominator.value` is the entire calculation - there is no
hidden extra scaling factor a reader would need to know about separately.
"""

from app.methodology.dto import MetricEstimate
from app.models.enums import MetricStatus, NormalizationBasis
from app.schemas.common import Denominator, NormalizedMetricRange
from app.schemas.workload import WorkloadInput

_TOKENS_PER_UNIT = 1000.0
_SECONDS_PER_MINUTE = 60.0


def resolve_denominator(workload: WorkloadInput) -> Denominator | None:
    """Determines the normalization denominator, if any, from the
    quantity fields actually populated on the workload - never from its
    activity_type/modality alone, so this stays generic across the
    existing taxonomy instead of hard-coding a per-activity mapping.

    Checked in a fixed, documented priority order (tokens, image, video,
    audio) since a workload is normally shaped for exactly one of these;
    the order only matters for the rare case where more than one
    quantity field happens to be populated at once.
    """
    total_tokens = (workload.input_tokens or 0) + (workload.output_tokens or 0)
    if total_tokens > 0:
        return Denominator(
            value=total_tokens / _TOKENS_PER_UNIT,
            unit="1K tokens",
            basis=NormalizationBasis.INPUT_PLUS_OUTPUT,
        )

    if workload.image_count and workload.image_count > 0:
        return Denominator(
            value=float(workload.image_count),
            unit="image",
            basis=NormalizationBasis.IMAGE_COUNT,
        )

    if workload.video_seconds and workload.video_seconds > 0:
        return Denominator(
            value=float(workload.video_seconds),
            unit="second",
            basis=NormalizationBasis.VIDEO_SECONDS,
        )

    if workload.audio_seconds and workload.audio_seconds > 0:
        return Denominator(
            value=workload.audio_seconds / _SECONDS_PER_MINUTE,
            unit="minute",
            basis=NormalizationBasis.AUDIO_MINUTES,
        )

    return None


def normalize_metric(
    metric: MetricEstimate, methodology_version: str | None, denominator: Denominator
) -> NormalizedMetricRange:
    """Divides one metric's min/max independently by the denominator.

    Preserves status/confidence/evidence_level/accounting_boundary from
    the raw estimate unchanged - normalization changes scale, never
    evidentiary basis. An insufficient_data raw metric normalizes to an
    insufficient_data range with min/max absent, never to zero and never
    to a value implying more certainty than the raw estimate supports.
    """
    unit = f"{metric.unit} per {denominator.unit}"
    if metric.status == MetricStatus.INSUFFICIENT_DATA:
        return NormalizedMetricRange(
            status=MetricStatus.INSUFFICIENT_DATA,
            min=None,
            max=None,
            unit=unit,
            confidence=metric.confidence,
            evidence_level=metric.evidence_level,
            methodology_version=methodology_version,
            accounting_boundary=metric.accounting_boundary,
        )

    return NormalizedMetricRange(
        status=metric.status,
        min=(metric.min / denominator.value) if metric.min is not None else None,
        max=(metric.max / denominator.value) if metric.max is not None else None,
        unit=unit,
        confidence=metric.confidence,
        evidence_level=metric.evidence_level,
        methodology_version=methodology_version,
        accounting_boundary=metric.accounting_boundary,
    )
