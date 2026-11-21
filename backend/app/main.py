"""
FastAPI Application Entry Point.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException, ErrorEnvelope, ErrorBody
from backend.app.api.v1.endpoints import documents, check

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DocumentProcessingException)
async def document_processing_exception_handler(request: Request, exc: DocumentProcessingException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=f"req_{request.scope.get('asgi', {}).get('version', 'local')}",
            )
        ).model_dump(),
    )


# Include v1 routers
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(check.router, prefix=settings.API_V1_STR)


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": "development",
    }
