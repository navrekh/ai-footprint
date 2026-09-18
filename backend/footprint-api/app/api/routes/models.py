from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db_session
from app.schemas.model import ModelRead
from app.services.model_service import ModelService

router = APIRouter()


@router.get(
    "/models",
    response_model=list[ModelRead],
    tags=["registry"],
    summary="List registered models, filterable by provider/modality/status",
    description="Public, no authentication required.",
)
async def list_models(
    provider: str | None = Query(default=None, description="Filter by provider id"),
    modality: str | None = Query(default=None, description="Filter by supported modality"),
    status: str | None = Query(default=None, description="Filter by model status"),
    db: AsyncSession = Depends(get_db_session),
) -> list[ModelRead]:
    models = await ModelService(db).list_models(
        provider_id=provider, modality=modality, status=status
    )
    return [ModelRead.model_validate(model) for model in models]
