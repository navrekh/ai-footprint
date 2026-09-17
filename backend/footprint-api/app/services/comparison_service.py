from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, BenchmarkNotFoundError, InvalidWorkloadError
from app.core.request_id import get_request_id
from app.methodology.benchmarks import BenchmarkDefinition, get_benchmark
from app.methodology.normalization import normalize_metric, resolve_denominator
from app.methodology.pipeline import EstimationPipeline
from app.schemas.common import ComparisonCandidate, ErrorDetail, NormalizedResourceIntensity
from app.schemas.compare import ComparisonResultItem
from app.schemas.workload import WorkloadInput
from app.services.estimate_service import build_estimate_response


class ComparisonService:
    """Backs POST /v1/compare and POST /v1/benchmarks/run.

    Both endpoints evaluate one workload definition against multiple
    provider/model candidates. `_run_comparison` is the single shared
    execution path (sprint 4 FRD section 35.2/35.6, ARCHITECTURE.md
    ADR-007/ADR-008): each candidate is estimated independently through
    the existing EstimationPipeline, candidates are never aggregated or
    ranked against each other, and a candidate's failure never affects
    any other candidate's result. This class does not implement a second
    estimation engine - it only sequences existing pipeline calls and
    reuses the existing per-item AppError -> ErrorDetail translation
    already established by BatchService.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._pipeline = EstimationPipeline(db)

    async def compare(
        self, base_fields: dict, candidates: list[ComparisonCandidate]
    ) -> list[ComparisonResultItem]:
        return await self._run_comparison(base_fields, candidates)

    async def run_benchmark(
        self, benchmark_id: str, candidates: list[ComparisonCandidate]
    ) -> tuple[BenchmarkDefinition, list[ComparisonResultItem]]:
        definition = get_benchmark(benchmark_id)
        if definition is None:
            raise BenchmarkNotFoundError(f"Benchmark '{benchmark_id}' was not found.")

        base_fields = {
            "modality": definition.modality,
            "activity_type": definition.activity_type,
            **definition.parameters,
        }
        results = await self._run_comparison(base_fields, candidates)
        return definition, results

    async def _run_comparison(
        self, base_fields: dict, candidates: list[ComparisonCandidate]
    ) -> list[ComparisonResultItem]:
        results: list[ComparisonResultItem] = []

        for candidate in candidates:
            try:
                workload = WorkloadInput(
                    provider=candidate.provider,
                    model=candidate.model,
                    model_version=candidate.model_version,
                    **base_fields,
                )
            except ValidationError as exc:
                results.append(
                    self._failure(candidate, InvalidWorkloadError(str(exc.errors()[0]["msg"])))
                )
                continue

            try:
                result = await self._pipeline.run(workload)
            except AppError as exc:
                results.append(self._failure(candidate, exc))
                continue

            estimate = build_estimate_response(result)
            normalized: NormalizedResourceIntensity | None = None
            denominator = resolve_denominator(workload)
            if denominator is not None:
                normalized = NormalizedResourceIntensity(
                    denominator=denominator,
                    energy=normalize_metric(result.energy, result.methodology_version, denominator),
                    water=normalize_metric(result.water, result.methodology_version, denominator),
                    carbon=normalize_metric(result.carbon, result.methodology_version, denominator),
                )

            results.append(
                ComparisonResultItem(
                    candidate=candidate,
                    status="success",
                    resolved=ComparisonCandidate(
                        provider=result.provider,
                        model=result.model,
                        model_version=result.model_version,
                    ),
                    estimate=estimate,
                    normalized=normalized,
                )
            )

        return results

    @staticmethod
    def _failure(candidate: ComparisonCandidate, exc: AppError) -> ComparisonResultItem:
        return ComparisonResultItem(
            candidate=candidate,
            status="failed",
            error=ErrorDetail(
                code=exc.code.value, message=exc.message, request_id=get_request_id() or ""
            ),
        )
