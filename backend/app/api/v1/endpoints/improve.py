"""
Writing Improver Router.
Exposes POST /api/v1/improve.
"""

import logging
from fastapi import APIRouter, Request, HTTPException, status
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException, ErrorEnvelope
from backend.app.core.security import get_limiter
from backend.app.models.improver import ImproveRequest, ImproveResponse
from backend.app.services.improver.pipeline import run_improver_pipeline

logger = logging.getLogger(__name__)
limiter = get_limiter()
router = APIRouter(prefix="", tags=["improver"])


@router.post(
    "/improve",
    response_model=ImproveResponse,
    responses={
        400: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
        502: {"model": ErrorEnvelope},
        504: {"model": ErrorEnvelope},
    },
)
@limiter.limit("10/minute")
async def improve_text(payload: ImproveRequest, request: Request) -> ImproveResponse:
    """
    Improves text flow, clarity, and readability across six modes while preserving protected spans.
    Does not log user text content.
    """
    logger.info("Received improve request (mode=%s, provider=%s)", payload.mode, payload.provider)

    try:
        response = await run_improver_pipeline(
            text=payload.text,
            mode=payload.mode,
            provider_override=payload.provider,
            run_verification=payload.run_verification,
            enable_nli=payload.enable_nli,
        )
        logger.info(
            "Improvement complete: revision_id=%s, mode=%s, paragraphs=%d, cost=$%.6f",
            response.revision_id,
            response.mode,
            len(response.paragraphs),
            response.usage.estimated_cost_usd,
        )
        return response
    except DocumentProcessingException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in improve endpoint: %s", str(exc))
        raise DocumentProcessingException(
            status_code=500,
            code="IMPROVER_ERROR",
            message=f"An error occurred while improving text: {str(exc)}",
        )
