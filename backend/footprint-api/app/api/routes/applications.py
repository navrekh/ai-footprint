from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationRead,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService
from app.services.auth_service import AuthContext
from app.services.tenant_context import resolve_optional_project_filter, resolve_target_project_id

router = APIRouter()


@router.post(
    "/applications",
    response_model=ApplicationRead,
    tags=["applications"],
    summary="Create an application within an authorized project",
)
async def create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApplicationRead:
    project_id = await resolve_target_project_id(db, auth, payload.project_id)
    application = await ApplicationService(db).create(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        environment=payload.environment.value if payload.environment else None,
    )
    return ApplicationRead.model_validate(application)


@router.get(
    "/applications",
    response_model=ApplicationListResponse,
    tags=["applications"],
    summary="List applications visible to the authenticated organization/project",
)
async def list_applications(
    project: str | None = Query(default=None, description="Filter by project id"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApplicationListResponse:
    project_filter = resolve_optional_project_filter(auth, project)
    items, total = await ApplicationService(db).list_for_scope(
        auth.organization.id, project_id=project_filter, limit=limit, offset=offset
    )
    return ApplicationListResponse(
        items=[ApplicationRead.model_validate(a) for a in items], total=total
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationRead,
    tags=["applications"],
    summary="Get an application owned by the authenticated organization/project",
)
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApplicationRead:
    project_filter = resolve_optional_project_filter(auth, None)
    application = await ApplicationService(db).get_owned(
        auth.organization.id, application_id, project_id=project_filter
    )
    return ApplicationRead.model_validate(application)


@router.patch(
    "/applications/{application_id}",
    response_model=ApplicationRead,
    tags=["applications"],
    summary="Update an application owned by the authenticated organization/project",
)
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApplicationRead:
    project_filter = resolve_optional_project_filter(auth, None)
    application = await ApplicationService(db).update(
        auth.organization.id, application_id, payload, project_id=project_filter
    )
    return ApplicationRead.model_validate(application)
