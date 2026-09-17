from fastapi import APIRouter

from app.api.routes import (
    api_keys,
    applications,
    batch,
    benchmarks,
    compare,
    estimate,
    estimates,
    events,
    health,
    methodology,
    models,
    organizations,
    projects,
    providers,
    usage,
    workloads,
)

api_router = APIRouter()
api_router.include_router(health.router)

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(organizations.router)
v1_router.include_router(projects.router)
v1_router.include_router(applications.router)
v1_router.include_router(api_keys.router)
v1_router.include_router(estimate.router)
v1_router.include_router(events.router)
v1_router.include_router(batch.router)
v1_router.include_router(workloads.router)
v1_router.include_router(estimates.router)
v1_router.include_router(usage.router)
v1_router.include_router(providers.router)
v1_router.include_router(models.router)
v1_router.include_router(methodology.router)
v1_router.include_router(compare.router)
v1_router.include_router(benchmarks.router)

api_router.include_router(v1_router)

__all__ = ["api_router"]
