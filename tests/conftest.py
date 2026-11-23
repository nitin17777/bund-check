"""
Shared pytest fixtures for BundCheck tests.

Key fixture: `test_app` — a FastAPI application instance with SlowAPIMiddleware
(BaseHTTPMiddleware-based) removed to avoid Starlette body-read deadlocks when
using httpx.AsyncClient with ASGITransport in sync test contexts.

Background: SlowAPIMiddleware extends BaseHTTPMiddleware, which buffers the
request body internally. With the ASGI transport used in tests, this causes
the request body stream to be consumed before the actual endpoint handler can
read it, resulting in an indefinite hang.

Solution: Create a test-only app that excludes SlowAPIMiddleware. Rate limiting
is not tested here (it is validated via integration tests with a live server).
"""

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi import Request
import httpx

from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException, ErrorEnvelope, ErrorBody
from backend.app.core.logging import configure_logging
from backend.app.core.security import SecurityHeadersMiddleware, get_limiter, rate_limit_exceeded_handler
from backend.app.core.task_manager import task_manager
from backend.app.api.v1.endpoints import documents, check, improve, verify, tasks
from backend.app.api.v1.endpoints.users import router as users_router
from backend.app.api.v1.endpoints.settings import router as settings_router
from backend.app.api.v1.endpoints import history, delete, export


def _build_test_app() -> FastAPI:
    """
    Build a test-only FastAPI application.
    Identical to main.py but WITHOUT SlowAPIMiddleware (BaseHTTPMiddleware).
    This avoids body-stream deadlocks when using httpx.AsyncClient in tests.
    """
    configure_logging(log_level="ERROR")  # reduce noise in tests

    test_app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    limiter = get_limiter()
    test_app.state.limiter = limiter

    # CORS
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://testserver"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID", "Authorization"],
        expose_headers=["X-Request-ID", "Retry-After", "Content-Disposition"],
        max_age=600,
    )

    # Security headers (pure ASGI — safe)
    test_app.add_middleware(SecurityHeadersMiddleware)

    # NOTE: SlowAPIMiddleware intentionally omitted to prevent TestClient deadlock

    @test_app.exception_handler(RateLimitExceeded)
    async def _handle_rate_limit(request: Request, exc: RateLimitExceeded):
        return await rate_limit_exceeded_handler(request, exc)

    @test_app.exception_handler(DocumentProcessingException)
    async def _doc_exc_handler(request: Request, exc: DocumentProcessingException):
        request_id = getattr(request.state, "request_id", None)
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

    test_app.include_router(documents.router, prefix=settings.API_V1_STR)
    test_app.include_router(check.router, prefix=settings.API_V1_STR)
    test_app.include_router(improve.router, prefix=settings.API_V1_STR)
    test_app.include_router(verify.router, prefix=settings.API_V1_STR)
    test_app.include_router(tasks.router, prefix=settings.API_V1_STR)
    test_app.include_router(users_router, prefix=settings.API_V1_STR)
    test_app.include_router(settings_router, prefix=settings.API_V1_STR)
    test_app.include_router(history.router, prefix=settings.API_V1_STR)
    test_app.include_router(delete.router, prefix=settings.API_V1_STR)
    test_app.include_router(export.router, prefix=settings.API_V1_STR)

    @test_app.get("/api/v1/health", tags=["health"])
    async def health_check_test():
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "active_tasks": task_manager.active_task_count,
        }

    return test_app


# Module-level singleton (built once per test session)
_TEST_APP = None


def get_test_app() -> FastAPI:
    global _TEST_APP
    if _TEST_APP is None:
        _TEST_APP = _build_test_app()
    return _TEST_APP


@pytest.fixture(scope="session")
def test_app():
    """FastAPI app instance without rate-limiting middleware."""
    return get_test_app()


@pytest.fixture(scope="session")
def api_client(test_app):
    """
    Synchronous httpx.Client backed by the test app (no SlowAPIMiddleware).
    Uses Starlette TestClient which handles sync-to-ASGI bridging correctly.
    Safe because the test app has no BaseHTTPMiddleware body-read issues.
    """
    from starlette.testclient import TestClient
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c
