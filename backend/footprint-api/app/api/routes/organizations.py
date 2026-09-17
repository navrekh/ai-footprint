from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.core.errors import NotFoundError
from app.schemas.organization import (
    OrganizationBootstrapResponse,
    OrganizationCreate,
    OrganizationRead,
)
from app.schemas.project import ProjectRead
from app.services.auth_service import AuthContext
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.post(
    "/organizations",
    response_model=OrganizationBootstrapResponse,
    tags=["organizations"],
    summary="Sign up: create an organization with a default project and first API key",
)
async def create_organization(
    payload: OrganizationCreate, db: AsyncSession = Depends(get_db_session)
) -> OrganizationBootstrapResponse:
    organization, project, api_key = await OrganizationService(db).create_with_bootstrap(
        payload.name
    )
    return OrganizationBootstrapResponse(
        organization=OrganizationRead.model_validate(organization),
        project=ProjectRead.model_validate(project),
        api_key=api_key,
    )


@router.get(
    "/organizations/{organization_id}",
    response_model=OrganizationRead,
    tags=["organizations"],
    summary="Get the authenticated caller's own organization",
)
async def get_organization(
    organization_id: str,
    auth: AuthContext = Depends(get_auth_context),
) -> OrganizationRead:
    if organization_id != auth.organization.id:
        # Never confirm whether another organization exists.
        raise NotFoundError("Organization not found.")
    return OrganizationRead.model_validate(auth.organization)
