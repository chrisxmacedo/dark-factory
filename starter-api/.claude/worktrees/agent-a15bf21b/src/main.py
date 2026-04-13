from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.cache import close_redis, init_redis
from src.config import get_settings
from src.database import engine
from src.middleware.content_type import ContentTypeMiddleware
from src.middleware.idempotency import IdempotencyMiddleware
from src.middleware.logging import configure_logging
from src.middleware.rate_limit import get_rate_limit_key, rate_limit_exceeded_handler
from src.routers import health, schema
from src.telemetry import init_telemetry, instrument_app, shutdown_telemetry

settings = get_settings()
logger = structlog.get_logger()

# ── Sentry ──────────────────────────────────────────────────────────────────

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment=settings.app_env,
        send_default_pii=False,
    )

# Rate limiter — keys on user ID, falls back to IP for public endpoints
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri=settings.redis_url or "memory://",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.log_level)
    init_telemetry(settings)
    instrument_app(app, engine.sync_engine)
    await init_redis()
    logger.info("startup", env=settings.app_env)
    yield
    await close_redis()
    shutdown_telemetry()
    await engine.dispose()
    logger.info("shutdown")


app = FastAPI(
    title="starter-api",
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan,
)

# ── Middleware (LIFO order: last added = first executed) ────────────────────

# 4. Idempotency (Redis-backed, pure ASGI)
app.add_middleware(IdempotencyMiddleware)

# 3. Content-type enforcement (pure ASGI)
app.add_middleware(ContentTypeMiddleware)

# 2. Rate limiting
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_exceeded_handler,
)
app.add_middleware(SlowAPIMiddleware)

# 1. CORS (innermost — applied closest to the route handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail if isinstance(exc.detail, str) else "error",
                "message": exc.detail
                if isinstance(exc.detail, str)
                else str(exc.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": str(exc.errors()),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    sentry_sdk.capture_exception(exc)
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
            }
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(schema.router)

# Add new routers here:
# from src.routers import items
# app.include_router(items.router, prefix="/items")
