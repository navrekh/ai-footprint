from app.methodology.confidence import ConfidenceEngine
from app.methodology.dto import MetricEstimate
from app.models.enums import MetricStatus


def determine_metric_status(total: int, measured: int) -> MetricStatus:
    """The shared ok/partial/insufficient_data decision used everywhere a
    metric is aggregated across multiple workloads (batch estimation,
    usage intelligence): no measured value at all -> insufficient_data;
    every workload measured -> ok; anything in between -> partial. A
    partial aggregate must never be indistinguishable from a complete one.
    """
    if measured == 0:
        return MetricStatus.INSUFFICIENT_DATA
    if measured == total:
        return MetricStatus.OK
    return MetricStatus.PARTIAL


class UncertaintyEngine:
    """Propagates/aggregates uncertainty ranges for a metric.

    For additive composite workloads (batches, coding-agent sessions),
    minimums are summed and maximums are summed independently - never
    averaged, and never collapsed into a single false-precision point
    value (FRD section 21, sprint brief section 22).

    A partial aggregate must never look like a complete one (sprint
    review, item 3): the returned status reflects how many of the input
    estimates actually contributed a measured value -

    - none measured   -> insufficient_data (min/max are None)
    - some measured    -> partial (min/max sum only the measured ones,
                          and total_workloads/measured_workloads record
                          exactly how many)
    - all measured      -> ok

    Confidence, evidence level, accounting boundary and assumptions from
    the contributing estimates are combined (not dropped) - see item 4.

    For a single workload this still runs as an explicit pipeline stage
    (called with a one-item list) between the per-metric estimators and
    the confidence engine; with one input it simply reduces to ok/
    insufficient_data (a single estimate can never be "partial").
    """

    @staticmethod
    def aggregate(estimates: list[MetricEstimate], unit: str) -> MetricEstimate:
        total = len(estimates)
        available = [e for e in estimates if e.status == MetricStatus.OK]
        measured = len(available)

        status = determine_metric_status(total, measured)
        if status == MetricStatus.INSUFFICIENT_DATA:
            return MetricEstimate(
                status=status,
                unit=unit,
                total_workloads=total,
                measured_workloads=0,
            )

        confidences = [e.confidence for e in available if e.confidence]
        evidence_levels = [e.evidence_level for e in available if e.evidence_level is not None]
        boundaries = {e.accounting_boundary for e in available if e.accounting_boundary}
        assumptions = sorted({a for e in available for a in e.assumptions})
        limitations = sorted({limitation for e in available for limitation in e.limitations})

        return MetricEstimate(
            status=status,
            unit=unit,
            min=sum(e.min or 0.0 for e in available),
            max=sum(e.max or 0.0 for e in available),
            confidence=ConfidenceEngine.combine(confidences) if confidences else None,
            evidence_level=(
                ConfidenceEngine.combine_evidence_levels(evidence_levels)
                if evidence_levels
                else None
            ),
            accounting_boundary=next(iter(boundaries)) if len(boundaries) == 1 else None,
            assumptions=assumptions,
            limitations=limitations,
            total_workloads=total,
            measured_workloads=measured,
        )
