from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidWorkloadError
from app.db.base import utcnow
from app.methodology.pipeline import EstimationPipeline
from app.models.estimate import Estimate
from app.models.workload import AIWorkload
from app.schemas.workload import EventCreateRequest


class WorkloadService:
    """Backs POST /v1/events: persists the AIWorkload and its Estimate.

    If the provider/model cannot be resolved at all, nothing is
    persisted and the underlying AppError propagates. If the provider and
    model resolve but no methodology factor exists, the workload is still
    persisted with an Estimate carrying insufficient_data metrics
    (ARCHITECTURE.md section 18 - "preserve the workload event if valid").
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._pipeline = EstimationPipeline(db)

    async def create_event(
        self, *, organization_id: str, project_id: str, payload: EventCreateRequest
    ) -> tuple[AIWorkload, Estimate]:
        if payload.parent_workload_id:
            await self._ensure_parent_in_organization(payload.parent_workload_id, organization_id)

        result = await self._pipeline.run(payload)

        workload = AIWorkload(
            organization_id=organization_id,
            project_id=project_id,
            provider=payload.provider.strip().lower(),
            model=payload.model,
            modality=payload.modality.value,
            activity_type=payload.activity_type.value,
            timestamp=payload.timestamp or utcnow(),
            input_tokens=payload.input_tokens,
            output_tokens=payload.output_tokens,
            image_count=payload.image_count,
            image_width=payload.image_width,
            image_height=payload.image_height,
            video_seconds=payload.video_seconds,
            video_resolution=payload.video_resolution,
            audio_seconds=payload.audio_seconds,
            tool_calls=payload.tool_calls,
            duration_seconds=payload.duration_seconds,
            parent_workload_id=payload.parent_workload_id,
            workload_metadata=payload.metadata,
        )
        self._db.add(workload)
        await self._db.flush()

        estimate = Estimate(
            workload_id=workload.id,
            energy_status=result.energy.status.value,
            energy_min_wh=result.energy.min,
            energy_max_wh=result.energy.max,
            water_status=result.water.status.value,
            water_min_ml=result.water.min,
            water_max_ml=result.water.max,
            carbon_status=result.carbon.status.value,
            carbon_min_g=result.carbon.min,
            carbon_max_g=result.carbon.max,
            confidence=result.confidence.value if result.confidence else None,
            evidence_level=result.evidence_level,
            accounting_boundary=result.accounting_boundary,
            methodology_version=result.methodology_version,
            assumptions=result.assumptions,
        )
        self._db.add(estimate)
        await self._db.commit()
        await self._db.refresh(workload)
        await self._db.refresh(estimate)
        return workload, estimate

    async def _ensure_parent_in_organization(self, parent_id: str, organization_id: str) -> None:
        result = await self._db.execute(select(AIWorkload).where(AIWorkload.id == parent_id))
        parent = result.scalar_one_or_none()
        if parent is None or parent.organization_id != organization_id:
            raise InvalidWorkloadError(
                "parent_workload_id does not reference a workload in this organization."
            )
