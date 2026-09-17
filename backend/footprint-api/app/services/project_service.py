from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.slugs import allocate_unique_slug
from app.models.project import Project
from app.schemas.project import ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self, organization_id: str, name: str, description: str | None
    ) -> Project:
        async def stage_project(candidate_slug: str) -> Project:
            project = Project(
                organization_id=organization_id,
                name=name,
                slug=candidate_slug,
                description=description,
            )
            self._db.add(project)
            await self._db.flush()
            return project

        project = await allocate_unique_slug(
            self._db,
            name=name,
            fallback="project",
            constraint_name="uq_project_organization_slug",
            try_insert=stage_project,
        )
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def list_for_organization(
        self, organization_id: str, *, limit: int, offset: int
    ) -> tuple[list[Project], int]:
        total = (
            await self._db.execute(
                select(func.count())
                .select_from(Project)
                .where(Project.organization_id == organization_id)
            )
        ).scalar_one()
        result = await self._db.execute(
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc(), Project.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def get_owned(self, organization_id: str, project_id: str) -> Project:
        result = await self._db.execute(
            select(Project).where(
                Project.id == project_id, Project.organization_id == organization_id
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            # Never distinguish "belongs to another org" from "does not
            # exist" (sprint review, tenant isolation).
            raise NotFoundError("Project not found.")
        return project

    async def update(
        self, organization_id: str, project_id: str, payload: ProjectUpdate
    ) -> Project:
        project = await self.get_owned(organization_id, project_id)
        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.status is not None:
            project.status = payload.status.value
        await self._db.commit()
        await self._db.refresh(project)
        return project
