from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    ApplicationNotFoundError,
    ApplicationProjectMismatchError,
    NotFoundError,
)
from app.core.slugs import allocate_unique_slug
from app.models.application import Application
from app.models.project import Project
from app.schemas.application import ApplicationUpdate


class ApplicationService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        project_id: str,
        name: str,
        description: str | None,
        environment: str | None,
    ) -> Application:
        async def stage_application(candidate_slug: str) -> Application:
            application = Application(
                project_id=project_id,
                name=name,
                slug=candidate_slug,
                description=description,
                environment=environment,
            )
            self._db.add(application)
            await self._db.flush()
            return application

        application = await allocate_unique_slug(
            self._db,
            name=name,
            fallback="app",
            constraint_name="uq_application_project_slug",
            try_insert=stage_application,
        )
        await self._db.commit()
        await self._db.refresh(application)
        return application

    async def list_for_scope(
        self, organization_id: str, *, project_id: str | None, limit: int, offset: int
    ) -> tuple[list[Application], int]:
        filters = [Project.organization_id == organization_id]
        if project_id is not None:
            filters.append(Application.project_id == project_id)

        total = (
            await self._db.execute(
                select(func.count())
                .select_from(Application)
                .join(Project, Project.id == Application.project_id)
                .where(*filters)
            )
        ).scalar_one()
        result = await self._db.execute(
            select(Application)
            .join(Project, Project.id == Application.project_id)
            .where(*filters)
            .order_by(Application.created_at.desc(), Application.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def get_owned(
        self, organization_id: str, application_id: str, *, project_id: str | None = None
    ) -> Application:
        """Fetches a single application scoped to organization_id and,
        for a project-scoped key, also to project_id - the same rule
        applied to workload/estimate single-record reads (sprint 2
        follow-up review), so an application belonging to a different
        project can never be read by a key scoped to another project.
        """
        conditions = [Application.id == application_id, Project.organization_id == organization_id]
        if project_id is not None:
            conditions.append(Application.project_id == project_id)
        result = await self._db.execute(
            select(Application)
            .join(Project, Project.id == Application.project_id)
            .where(*conditions)
        )
        application = result.scalar_one_or_none()
        if application is None:
            # Never distinguish "belongs to another project/org" from
            # "does not exist" (sprint review, tenant isolation).
            raise NotFoundError("Application not found.")
        return application

    async def update(
        self,
        organization_id: str,
        application_id: str,
        payload: ApplicationUpdate,
        *,
        project_id: str | None = None,
    ) -> Application:
        application = await self.get_owned(organization_id, application_id, project_id=project_id)
        if payload.name is not None:
            application.name = payload.name
        if payload.description is not None:
            application.description = payload.description
        if payload.status is not None:
            application.status = payload.status.value
        if payload.environment is not None:
            application.environment = payload.environment.value
        await self._db.commit()
        await self._db.refresh(application)
        return application

    async def resolve_for_workload(
        self, organization_id: str, project_id: str, application_id: str
    ) -> Application:
        """Resolves an application_id supplied on a workload/event
        submission (FRD section 19), enforcing that it belongs to the
        target project.

        Distinguishes "does not exist in this organization at all"
        (opaque ApplicationNotFoundError - never reveals whether it
        exists in a different organization) from "exists in this
        organization but a different project" (explicit
        ApplicationProjectMismatchError - not a tenant leak, since it is
        scoped to the caller's own organization, matching the existing
        ForbiddenError precedent for a project-scoped key's own project
        mismatch in tenant_context.resolve_target_project_id).
        """
        application = await self._db.get(Application, application_id)
        if application is None:
            raise ApplicationNotFoundError()

        project = await self._db.get(Project, application.project_id)
        if project is None or project.organization_id != organization_id:
            raise ApplicationNotFoundError()

        if application.project_id != project_id:
            raise ApplicationProjectMismatchError()

        return application
