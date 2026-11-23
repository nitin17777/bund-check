"""
FastAPI Application Entry Point — Phase 9 hardened.

Security additions:
- SecurityHeadersMiddleware: adds HSTS, CSP, X-Frame-Options, nosniff, Permissions-Policy,
  Cache-Control: no-store on all /api/ endpoints.
- slowapi rate limiter: per-IP token-bucket; global default + per-endpoint overrides.
- structlog: content-free structured logging configured at startup.
- Task router: GET /api/v1/tasks/{task_id} for async polling.
- Tightened CORS: allow_origins restricted from "*" to configured list.
- Request-ID injection: each request gets an X-Request-ID header echoed in responses.
"""

import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler  # noqa: F401 (registered below)
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException, ErrorEnvelope, ErrorBody
from backend.app.core.logging import configure_logging, get_logger
from backend.app.core.security import SecurityHeadersMiddleware, get_limiter, rate_limit_exceeded_handler
from backend.app.core.task_manager import task_manager
from backend.app.api.v1.endpoints import documents, check, improve, verify, tasks
from backend.app.api.v1.endpoints.users import router as users_router
from backend.app.api.v1.endpoints.settings import router as settings_router
from backend.app.api.v1.endpoints import history, delete, export

# ---------------------------------------------------------------------------
# Logging setup (must run before any logger.getLogger calls)
# ---------------------------------------------------------------------------
configure_logging(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (module-level so endpoints can import it)
# ---------------------------------------------------------------------------
limiter = get_limiter()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("bundcheck_startup", version=settings.VERSION, environment=settings.ENVIRONMENT)
    yield
    logger.info("bundcheck_shutdown")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    description=(
        "BundCheck API — probabilistic AI-pattern detection and writing improvement. "
        "Detection outputs are statistical estimates and do NOT prove authorship."
    ),
    lifespan=lifespan,
)

# Attach rate limiter state to app for slowapi middleware
app.state.limiter = limiter

# ---------------------------------------------------------------------------
# Middleware stack (applied in reverse order of registration)
# ---------------------------------------------------------------------------

# 1. CORS — allow configured origins only (not wildcard in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=False,  # No session cookies; API-key or anon
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID", "Authorization"],
    expose_headers=["X-Request-ID", "Retry-After", "Content-Disposition"],
    max_age=600,
)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. slowapi rate limiting
app.add_middleware(SlowAPIMiddleware)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RateLimitExceeded)
async def _handle_rate_limit(request: Request, exc: RateLimitExceeded):
    return await rate_limit_exceeded_handler(request, exc)


@app.exception_handler(DocumentProcessingException)
async def document_processing_exception_handler(request: Request, exc: DocumentProcessingException):
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
            )
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(check.router, prefix=settings.API_V1_STR)
app.include_router(improve.router, prefix=settings.API_V1_STR)
app.include_router(verify.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(history.router, prefix=settings.API_V1_STR)
app.include_router(delete.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", tags=["health"])
@limiter.limit("60/minute")
async def health_check(request: Request):
    """
    Service health check.
    Returns version, environment, and task manager statistics.
    Does NOT return model memory usage (would require psutil/torch overhead on each call).
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "active_tasks": task_manager.active_task_count,
    }


@app.get("/api/v1/test-rate-limit", include_in_schema=False)
@limiter.limit("2/minute")
async def _rate_limit_probe(request: Request):
    """Internal probe endpoint for rate-limiter verification in tests."""
    return {"status": "ok"}



