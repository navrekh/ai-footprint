from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_auth_context
from app.api.dependencies.db import get_db_session
from app.schemas.api_key import (
    ApiKeyCreated,
    ApiKeyCreateRequest,
    ApiKeyListResponse,
    ApiKeyRead,
)
from app.services.api_key_service import ApiKeyService
from app.services.auth_service import AuthContext
from app.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "/api-keys",
    response_model=ApiKeyCreated,
    tags=["api-keys"],
    summary="Create a new API key (organization-level, or scoped to one project)",
)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApiKeyCreated:
    if payload.project_id is not None:
        # Validates the project belongs to the caller's organization -
        # raises NotFoundError otherwise (never leaks cross-tenant existence).
        await ProjectService(db).get_owned(auth.organization.id, payload.project_id)

    return await ApiKeyService(db).create(
        organization_id=auth.organization.id,
        project_id=payload.project_id,
        name=payload.name,
        expires_at=payload.expires_at,
    )


@router.get(
    "/api-keys",
    response_model=ApiKeyListResponse,
    tags=["api-keys"],
    summary="List API keys belonging to the authenticated organization",
)
async def list_api_keys(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApiKeyListResponse:
    items, total = await ApiKeyService(db).list_for_organization(
        auth.organization.id, limit=limit, offset=offset
    )
    return ApiKeyListResponse(items=[ApiKeyRead.model_validate(k) for k in items], total=total)


@router.post(
    "/api-keys/{api_key_id}/revoke",
    response_model=ApiKeyRead,
    tags=["api-keys"],
    summary="Revoke an API key belonging to the authenticated organization",
)
async def revoke_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(get_auth_context),
) -> ApiKeyRead:
    api_key = await ApiKeyService(db).revoke(auth.organization.id, api_key_id)
    return ApiKeyRead.model_validate(api_key)
