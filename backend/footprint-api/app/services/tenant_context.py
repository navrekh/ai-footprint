from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, MissingParameterError
from app.services.auth_service import AuthContext
from app.services.project_service import ProjectService


async def resolve_target_project_id(
    db: AsyncSession, auth: AuthContext, requested_project_id: str | None
) -> str:
    """Resolves which project a write (e.g. POST /v1/events) targets.

    A project-scoped key always targets its own project (and rejects any
    explicit project_id that does not match it); an organization-level
    key must specify one explicitly, which is then validated to belong
    to the caller's organization.
    """
    if auth.project is not None:
        if requested_project_id is not None and requested_project_id != auth.project.id:
            raise ForbiddenError("This API key is scoped to a different project.")
        return auth.project.id

    if requested_project_id is None:
        raise MissingParameterError("project_id")

    # get_owned validates ownership, raising NotFoundError if the project
    # belongs to a different organization.
    project = await ProjectService(db).get_owned(auth.organization.id, requested_project_id)
    return project.id


def resolve_optional_project_filter(
    auth: AuthContext, requested_project_id: str | None
) -> str | None:
    """Resolves the project filter for a read (history) endpoint.

    A project-scoped key is always hard-limited to its own project,
    regardless of what filter it requests; an organization-level key may
    optionally filter by a project (ownership is validated by the
    history query itself scoping on organization_id).
    """
    if auth.project is not None:
        return auth.project.id
    return requested_project_id
