from app.methodology.dto import MetricEstimate
from app.models.enums import MetricStatus


class UncertaintyEngine:
    """Propagates/aggregates uncertainty ranges for a metric.

    For additive composite workloads (batches, coding-agent sessions),
    minimums are summed and maximums are summed independently - never
    averaged, and never collapsed into a single false-precision point
    value (FRD section 21, sprint brief section 22).

    For a single workload this is the identity operation over one range,
    which is why it still appears as an explicit pipeline stage between
    the per-metric estimators and the confidence engine.
    """

    @staticmethod
    def aggregate(estimates: list[MetricEstimate], unit: str) -> MetricEstimate:
        available = [e for e in estimates if e.status == MetricStatus.OK]
        if not available:
            return MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit=unit)

        return MetricEstimate(
            status=MetricStatus.OK,
            unit=unit,
            min=sum(e.min or 0.0 for e in available),
            max=sum(e.max or 0.0 for e in available),
        )
