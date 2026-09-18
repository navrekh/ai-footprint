from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_errors import is_unique_violation
from app.core.errors import InvalidWorkloadError
from app.db.base import utcnow
from app.methodology.pipeline import EstimationPipeline
from app.models.estimate import Estimate
from app.models.workload import AIWorkload
from app.schemas.workload import EventCreateRequest
from app.services.application_service import ApplicationService

_IDEMPOTENCY_CONSTRAINT_NAME = "uq_workload_project_idempotency_key"


class WorkloadService:
    """Backs POST /v1/events: persists the AIWorkload and its Estimate.

    Transaction boundary (sprint 2 review, item 18): validate -> resolve
    provider/model/methodology -> create workload -> create estimate ->
    one commit. If anything before the commit raises, nothing is
    persisted - there is no path that leaves a workload row without its
    estimate, or vice versa.

    Concurrent idempotency-key inserts (sprint 2 follow-up review, item 2):
    the pre-insert lookup is a convenience, not the authority - two
    requests can both pass it before either commits. The database unique
    constraint on (project_id, idempotency_key) is the actual authority;
    if the workload insert violates it, the transaction is rolled back
    and the now-visible winning row (and its estimate) is returned as an
    idempotent replay instead of surfacing a 500. Any other integrity
    error is re-raised unchanged.

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
    ) -> tuple[AIWorkload, Estimate, bool]:
        """Returns (workload, estimate, is_idempotent_replay)."""
        if payload.idempotency_key:
            existing = await self._find_existing_by_idempotency_key(
                project_id, payload.idempotency_key
            )
            if existing is not None:
                workload, estimate = existing
                return workload, estimate, True

        if payload.parent_workload_id:
            await self._ensure_parent_in_project(
                payload.parent_workload_id, organization_id, project_id
            )

        if payload.application_id:
            await ApplicationService(self._db).resolve_for_workload(
                organization_id, project_id, payload.application_id
            )

        result = await self._pipeline.run(payload)

        workload = AIWorkload(
            organization_id=organization_id,
            project_id=project_id,
            application_id=payload.application_id,
            provider=result.provider,
            model=result.model,
            model_version=result.model_version,
            modality=payload.modality.value,
            activity_type=payload.activity_type.value,
            timestamp=payload.timestamp or utcnow(),
            input_tokens=payload.input_tokens,
            output_tokens=payload.output_tokens,
            input_characters=payload.input_characters,
            output_characters=payload.output_characters,
            image_count=payload.image_count,
            image_width=payload.image_width,
            image_height=payload.image_height,
            video_seconds=payload.video_seconds,
            video_resolution=payload.video_resolution,
            audio_seconds=payload.audio_seconds,
            tool_calls=payload.tool_calls,
            duration_seconds=payload.duration_seconds,
            duration_ms=payload.duration_ms,
            parent_workload_id=payload.parent_workload_id,
            idempotency_key=payload.idempotency_key,
            workload_metadata=payload.metadata,
            client_context=(
                payload.client.model_dump(mode="json", exclude_none=True)
                if payload.client
                else None
            ),
        )
        try:
            self._db.add(workload)
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            if payload.idempotency_key and self._is_idempotency_key_conflict(exc):
                existing = await self._find_existing_by_idempotency_key(
                    project_id, payload.idempotency_key
                )
                if existing is not None:
                    winning_workload, winning_estimate = existing
                    return winning_workload, winning_estimate, True
            raise

        estimate = Estimate(
            workload_id=workload.id,
            provider=result.provider,
            model=result.model,
            model_version=result.model_version,
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
        return workload, estimate, False

    @staticmethod
    def _is_idempotency_key_conflict(exc: IntegrityError) -> bool:
        """True only for a violation of the idempotency unique constraint
        specifically - never a generic "some IntegrityError happened", so
        an unrelated constraint violation is never mistaken for a
        successful idempotent replay.
        """
        return is_unique_violation(exc, _IDEMPOTENCY_CONSTRAINT_NAME)

    async def _find_existing_by_idempotency_key(
        self, project_id: str, idempotency_key: str
    ) -> tuple[AIWorkload, Estimate] | None:
        workload = (
            await self._db.execute(
                select(AIWorkload).where(
                    AIWorkload.project_id == project_id,
                    AIWorkload.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if workload is None:
            return None
        estimate = (
            await self._db.execute(select(Estimate).where(Estimate.workload_id == workload.id))
        ).scalar_one_or_none()
        if estimate is None:
            return None
        return workload, estimate

    async def _ensure_parent_in_project(
        self, parent_id: str, organization_id: str, project_id: str
    ) -> None:
        """A parent workload must belong to the caller's own project.

        Checked in addition to organization_id (sprint 3 P0 fix): a
        project-scoped key must never be able to reference - and thereby
        confirm the existence of, or link lineage into - a workload
        belonging to a sibling project in the same organization. Kept as
        one opaque error (not a distinct "mismatch" code) since, unlike
        application_id, parent_workload_id has no legitimate cross-project
        use case for a project-scoped key to be told about explicitly.
        """
        result = await self._db.execute(select(AIWorkload).where(AIWorkload.id == parent_id))
        parent = result.scalar_one_or_none()
        if (
            parent is None
            or parent.organization_id != organization_id
            or parent.project_id != project_id
        ):
            raise InvalidWorkloadError(
                "parent_workload_id does not reference a workload in this project."
            )
