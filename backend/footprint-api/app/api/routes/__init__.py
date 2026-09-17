from fastapi import APIRouter

from app.api.routes import batch, estimate, events, health, methodology, models, providers

api_router = APIRouter()
api_router.include_router(health.router)

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(estimate.router)
v1_router.include_router(events.router)
v1_router.include_router(batch.router)
v1_router.include_router(providers.router)
v1_router.include_router(models.router)
v1_router.include_router(methodology.router)

api_router.include_router(v1_router)

__all__ = ["api_router"]
