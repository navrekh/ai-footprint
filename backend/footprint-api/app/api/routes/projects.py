from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.errors import ErrorCode
from app.core.openapi_docs import AUTH_ERRORS, error_responses
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectRead, ProjectUpdate
from app.services.auth_service import AuthContext
from app.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "/projects",
    response_model=ProjectRead,
    tags=["projects"],
    summary="Create a project in the authenticated organization",
    description="Creates a new Project owned by the authenticated key's organization.",
    responses=error_responses(*AUTH_ERRORS),
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ProjectRead:
    project = await ProjectService(db).create(
        auth.organization.id, payload.name, payload.description
    )
    return ProjectRead.model_validate(project)


@router.get(
    "/projects",
    response_model=ProjectListResponse,
    tags=["projects"],
    summary="List projects belonging to the authenticated organization",
    description="Limit/offset-paginated list of every project in the authenticated organization.",
    responses=error_responses(*AUTH_ERRORS),
)
async def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ProjectListResponse:
    items, total = await ProjectService(db).list_for_organization(
        auth.organization.id, limit=limit, offset=offset
    )
    return ProjectListResponse(
        items=[ProjectRead.model_validate(p) for p in items], total=total
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectRead,
    tags=["projects"],
    summary="Get a project owned by the authenticated organization",
    description="Returns one project. 404 if it does not belong to the authenticated organization.",
    responses=error_responses(*AUTH_ERRORS, ErrorCode.NOT_FOUND),
)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ProjectRead:
    project = await ProjectService(db).get_owned(auth.organization.id, project_id)
    return ProjectRead.model_validate(project)


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectRead,
    tags=["projects"],
    summary="Update a project owned by the authenticated organization",
    description="Updates mutable project fields. 404 if the project does not belong to the caller.",
    responses=error_responses(*AUTH_ERRORS, ErrorCode.NOT_FOUND),
)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ProjectRead:
    project = await ProjectService(db).update(auth.organization.id, project_id, payload)
    return ProjectRead.model_validate(project)
