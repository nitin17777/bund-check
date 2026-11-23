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


import uuid
from starlette.types import ASGIApp, Scope, Receive, Send


class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware that adds security response headers and X-Request-ID.
    Avoids Starlette BaseHTTPMiddleware request-body stream deadlocks on file uploads.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate X-Request-ID
        req_headers = dict(scope.get("headers", []))
        req_id = req_headers.get(b"x-request-id")
        if not req_id:
            req_id = f"req_{uuid.uuid4().hex[:12]}".encode("ascii")

        path = scope.get("path", "")

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                # Filter out any duplicate security headers
                existing_headers = message.get("headers", [])
                out_headers = [
                    (k, v) for k, v in existing_headers
                    if k.lower() not in (
                        b"x-request-id",
                        b"strict-transport-security",
                        b"x-content-type-options",
                        b"x-frame-options",
                        b"referrer-policy",
                        b"permissions-policy",
                        b"content-security-policy",
                        b"cache-control",
                    )
                ]
                # Inject security headers and Request ID
                out_headers.append((b"x-request-id", req_id))
                out_headers.append((b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload"))
                out_headers.append((b"x-content-type-options", b"nosniff"))
                out_headers.append((b"x-frame-options", b"DENY"))
                out_headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                out_headers.append((b"permissions-policy", b"microphone=(), camera=(), geolocation=(), payment=()"))

                # CSP
                if path in ("/docs", "/redoc") or path.startswith("/openapi"):
                    out_headers.append((b"content-security-policy", _CSP_DOCS.encode("ascii")))
                else:
                    out_headers.append((b"content-security-policy", _CSP_DEFAULT.encode("ascii")))

                # Cache control
                if path.startswith("/api/"):
                    out_headers.append((b"cache-control", _API_CACHE_CONTROL.encode("ascii")))

                message["headers"] = out_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
