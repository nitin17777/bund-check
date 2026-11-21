"""
Security hardening middleware and rate-limiter factory.

Components:
1. SecurityHeadersMiddleware — adds HTTP security response headers to every response:
   - Strict-Transport-Security (HSTS)
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - Referrer-Policy: strict-origin-when-cross-origin
   - Content-Security-Policy (restrictive default; relaxed for /docs)
   - Permissions-Policy: disables microphone, camera, geolocation
   - Cache-Control: no-store for API endpoints (prevents browsers caching document text)

2. get_limiter() — builds a slowapi Limiter instance for token-bucket rate limiting.
   Defaults configured in settings; individual endpoint limits applied via @limiter.limit().

3. rate_limit_exceeded_handler — RFC 7807 429 response handler for slowapi.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.app.core.errors import ErrorEnvelope, ErrorBody


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

def get_limiter() -> Limiter:
    """
    Returns a slowapi Limiter using the client's remote IP as the key.
    Default limits are applied per-endpoint via decorator.
    Storage backend: in-memory (suitable for single-process deployment).
    """
    return Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """RFC 7807-compliant 429 response when rate limit is exceeded."""
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code="TOO_MANY_REQUESTS",
            message=f"Rate limit exceeded: {exc.detail}. Please wait before retrying.",
            request_id=request.headers.get("x-request-id"),
        )
    )
    return JSONResponse(
        status_code=429,
        content=envelope.model_dump(),
        headers={"Retry-After": "60"},
    )


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

_API_CACHE_CONTROL = "no-store, no-cache, must-revalidate, private"

_CSP_DEFAULT = (
    "default-src 'none'; "
    "script-src 'none'; "
    "style-src 'none'; "
    "img-src 'none'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

_CSP_DOCS = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "frame-ancestors 'none';"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security-related HTTP response headers to every API response.
    Docs routes (/docs, /redoc, /openapi.json) get a relaxed CSP to allow Swagger UI.
    API endpoints get the strictest policy + Cache-Control: no-store.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        path = request.url.path

        # HSTS — only meaningful behind HTTPS but harmless otherwise
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "microphone=(), camera=(), geolocation=(), payment=()"
        )

        # Content-Security-Policy: relax for Swagger UI paths
        if path in ("/docs", "/redoc") or path.startswith("/openapi"):
            response.headers["Content-Security-Policy"] = _CSP_DOCS
        else:
            response.headers["Content-Security-Policy"] = _CSP_DEFAULT

        # Prevent browsers caching document text from API endpoints
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = _API_CACHE_CONTROL

        return response
