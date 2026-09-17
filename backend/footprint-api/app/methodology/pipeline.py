from sqlalchemy.ext.asyncio import AsyncSession

from app.methodology.confidence import ConfidenceEngine
from app.methodology.dto import EstimateResult
from app.methodology.estimators import CarbonEstimator, EnergyEstimator, WaterEstimator
from app.methodology.factor_repository import FactorRepository
from app.methodology.methodology_resolver import MethodologyResolver
from app.methodology.model_resolver import ModelResolver
from app.methodology.provider_resolver import ProviderResolver
from app.methodology.uncertainty import UncertaintyEngine
from app.methodology.validator import WorkloadValidator
from app.models.enums import MetricStatus
from app.schemas.workload import WorkloadInput


class EstimationPipeline:
    """Sequences the estimation stages exactly as described in
    ARCHITECTURE.md section 6:

    AIWorkload -> Validate -> Resolve Provider -> Resolve Model
      -> Resolve Methodology -> Resolve Factors -> Energy/Water/Carbon
      Estimate -> Uncertainty Propagation -> Confidence -> Estimate

    Each stage is its own independently testable class; this class only
    sequences them and must not contain calculation or resolution logic
    itself.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._validator = WorkloadValidator()
        self._provider_resolver = ProviderResolver(db)
        self._model_resolver = ModelResolver(db)
        self._methodology_resolver = MethodologyResolver(db)
        self._factor_repository = FactorRepository(db)
        self._energy_estimator = EnergyEstimator()
        self._water_estimator = WaterEstimator()
        self._carbon_estimator = CarbonEstimator()

    async def run(self, workload: WorkloadInput) -> EstimateResult:
        self._validator.validate(workload)

        provider = await self._provider_resolver.resolve(workload.provider)
        model = await self._model_resolver.resolve(
            provider, workload.model, workload.modality.value, workload.model_version
        )

        # The methodology registry is authoritative (sprint review, item 1):
        # a model may reference a methodology_version, but factors under
        # that version must never be used unless the Methodology record
        # itself actually exists. A dangling reference yields
        # insufficient_data for every metric, never a fabricated or
        # inferred methodology.
        methodology = await self._methodology_resolver.resolve(model.methodology_version)

        energy_factor = water_factor = carbon_factor = None
        if methodology is not None:
            energy_factor = await self._factor_repository.find_best_factor(
                metric="energy",
                provider=provider.id,
                model=model.name,
                modality=workload.modality.value,
                activity_type=workload.activity_type.value,
                methodology_version=methodology.version,
            )
            water_factor = await self._factor_repository.find_best_factor(
                metric="water",
                provider=provider.id,
                model=model.name,
                modality=workload.modality.value,
                activity_type=workload.activity_type.value,
                methodology_version=methodology.version,
            )
            carbon_factor = await self._factor_repository.find_best_factor(
                metric="carbon",
                provider=provider.id,
                model=model.name,
                modality=workload.modality.value,
                activity_type=workload.activity_type.value,
                methodology_version=methodology.version,
            )

        # UncertaintyEngine.aggregate() combines confidence/evidence/
        # assumptions metadata as well as min/max, even for a single-item
        # list, so the post-aggregation estimates already carry everything
        # needed for the top-level confidence/evidence combination below.
        energy = UncertaintyEngine.aggregate(
            [self._energy_estimator.estimate(energy_factor)], unit="Wh"
        )
        water = UncertaintyEngine.aggregate(
            [self._water_estimator.estimate(water_factor)], unit="mL"
        )
        carbon = UncertaintyEngine.aggregate(
            [self._carbon_estimator.estimate(carbon_factor)], unit="gCO2e"
        )

        available = [m for m in (energy, water, carbon) if m.status == MetricStatus.OK]
        confidence = ConfidenceEngine.combine([m.confidence for m in available if m.confidence])
        evidence_level = ConfidenceEngine.combine_evidence_levels(
            [m.evidence_level for m in available if m.evidence_level is not None]
        )
        accounting_boundary = available[0].accounting_boundary if available else None
        assumptions = sorted({a for m in available for a in m.assumptions})

        return EstimateResult(
            energy=energy,
            water=water,
            carbon=carbon,
            confidence=confidence,
            evidence_level=evidence_level,
            accounting_boundary=accounting_boundary,
            methodology_version=methodology.version if methodology else None,
            assumptions=assumptions,
        )
