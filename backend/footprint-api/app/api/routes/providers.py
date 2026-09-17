from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db_session
from app.schemas.provider import ProviderRead
from app.services.provider_service import ProviderService

router = APIRouter()


@router.get(
    "/providers",
    response_model=list[ProviderRead],
    tags=["registry"],
    summary="List registered AI providers",
)
async def list_providers(db: AsyncSession = Depends(get_db_session)) -> list[ProviderRead]:
    providers = await ProviderService(db).list_providers()
    return [ProviderRead.model_validate(provider) for provider in providers]
