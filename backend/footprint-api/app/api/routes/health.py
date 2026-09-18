from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    tags=["health"],
    summary="Public liveness check",
    description="Public, no authentication required. Always returns `{\"status\": \"ok\"}`.",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}
