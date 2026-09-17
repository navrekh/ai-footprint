import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import configure_logging, get_logger
from app.core.request_id import generate_request_id, get_request_id, set_request_id

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = get_logger("app.request")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "AI Footprint estimates the energy, water and carbon impact of AI workloads "
        "as ranges with confidence, evidence level and methodology version - never as "
        "fabricated exact measurements."
    ),
)


@app.middleware("http")
async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = generate_request_id()
    set_request_id(request_id)
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "unhandled_exception", extra={"request_id": request_id, "endpoint": request.url.path}
        )
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "An unexpected error occurred.",
                    "request_id": request_id,
                }
            },
        )

    response.headers["X-Request-ID"] = request_id
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
        },
    )
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = get_request_id() or generate_request_id()
    logger.warning(
        "app_error",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "error_code": exc.code.value,
            "status": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code.value, "message": exc.message, "request_id": request_id}
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = get_request_id() or generate_request_id()
    errors = exc.errors()
    code = (
        ErrorCode.MISSING_PARAMETER
        if any(e.get("type") == "missing" for e in errors)
        else ErrorCode.INVALID_REQUEST
    )
    message = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in errors)
    logger.warning(
        "validation_error",
        extra={"request_id": request_id, "endpoint": request.url.path, "error_code": code.value},
    )
    return JSONResponse(
        status_code=422,
        content={"error": {"code": code.value, "message": message, "request_id": request_id}},
    )


app.include_router(api_router)
