from app.methodology.dto import MetricEstimate
from app.models.enums import Confidence, MetricStatus
from app.models.methodology_factor import MethodologyFactor


class BaseMetricEstimator:
    """Shared logic for the per-metric estimators.

    A resolved factor's value_min/value_max are used directly as the
    estimate for a single workload event; per METHODOLOGY.md, factors are
    themselves the calibrated evidence (e.g. a provider-reported median
    per-prompt figure) rather than inputs to a further token/duration
    formula invented by this codebase.
    """

    metric: str
    unit: str

    def estimate(self, factor: MethodologyFactor | None) -> MetricEstimate:
        if factor is None:
            return MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit=self.unit)
        return MetricEstimate(
            status=MetricStatus.OK,
            unit=factor.unit,
            min=factor.value_min,
            max=factor.value_max,
            confidence=Confidence(factor.confidence),
            evidence_level=factor.evidence_level,
            accounting_boundary=factor.accounting_boundary,
            factor_id=factor.factor_id,
            assumptions=list(factor.assumptions or []),
            limitations=list(factor.limitations or []),
        )


class EnergyEstimator(BaseMetricEstimator):
    metric = "energy"
    unit = "Wh"


class WaterEstimator(BaseMetricEstimator):
    metric = "water"
    unit = "mL"


class CarbonEstimator(BaseMetricEstimator):
    metric = "carbon"
    unit = "gCO2e"
