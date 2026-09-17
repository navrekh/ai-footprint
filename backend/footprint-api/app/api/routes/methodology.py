from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db_session
from app.schemas.methodology import MethodologyRead
from app.services.methodology_service import MethodologyService

router = APIRouter()


@router.get(
    "/methodology",
    response_model=list[MethodologyRead],
    tags=["registry"],
    summary="List published methodology versions, assumptions, limitations and sources",
)
async def list_methodology(db: AsyncSession = Depends(get_db_session)) -> list[MethodologyRead]:
    methodologies = await MethodologyService(db).list_methodologies()
    return [MethodologyRead.model_validate(methodology) for methodology in methodologies]
