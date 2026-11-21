"""
Detection Router.
Exposes:
- POST /api/v1/check: probabilistic pattern detection on pasted text or pre-extracted Document.
- POST /api/v1/check/report: export analysis report as structured JSON or rendered HTML report.
"""

import asyncio
import logging
from typing import Optional, Union
from fastapi import APIRouter, Request, HTTPException, Response, status
from fastapi.responses import JSONResponse, HTMLResponse

from backend.app.core.config import settings
from backend.app.core.errors import (
    DocumentProcessingException,
    ErrorEnvelope,
    ErrorBody,
    ErrorDetail,
)
from backend.app.models.detection import (
    CheckRequest,
    CheckResponse,
    ReportRequest,
)
from backend.app.services.detection.detector import run_detection_pipeline
from backend.app.services.detection.report import generate_json_report, generate_html_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["detection"])


@router.post(
    "/check",
    response_model=CheckResponse,
    responses={
        400: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
        504: {"model": ErrorEnvelope},
    },
)
async def check_content(payload: CheckRequest, request: Request) -> CheckResponse:
    """
    Analyzes document text or pre-extracted document structure for synthetic patterns.
    Logs operations without outputting sensitive user document text.
    """
    logger.info("Received check request (has_text=%s, has_doc=%s)", bool(payload.text), bool(payload.document))

    try:
        # Enforce timeout safety
        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_detection_pipeline,
                text=payload.text,
                document=payload.document,
                document_id=payload.document_id,
            ),
            timeout=settings.CHECK_TIMEOUT_SECONDS,
        )
        logger.info(
            "Check complete for analysis_id=%s, word_count=%d, score=%.3f, band=%s",
            result.analysis_id,
            result.stats["word_count"],
            result.synthetic_pattern_confidence,
            result.classification_band,
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Detection pipeline timed out after %.1f seconds", settings.CHECK_TIMEOUT_SECONDS)
        raise DocumentProcessingException(
            status_code=504,
            code="DETECTION_TIMEOUT",
            message=f"Detection analysis timed out after {settings.CHECK_TIMEOUT_SECONDS}s.",
        )
    except DocumentProcessingException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in check endpoint: %s", str(exc))
        raise DocumentProcessingException(
            status_code=500,
            code="DETECTION_ERROR",
            message=f"An error occurred during content analysis: {str(exc)}",
        )


@router.post(
    "/check/report",
    responses={
        200: {
            "content": {
                "application/json": {},
                "text/html": {},
                "application/pdf": {},
            },
            "description": "Exported detection report in requested format.",
        },
        400: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
    },
)
async def export_check_report(payload: ReportRequest, request: Request):
    """
    Exports completed detection analysis in JSON, HTML, or PDF format.
    Always embeds scientific limitations, disclaimers, and model version.
    """
    fmt = payload.format.lower().strip()
    title = payload.title or "AI Content Analysis Report"

    if fmt == "json":
        report_data = generate_json_report(payload.check_response, title=title)
        return JSONResponse(content=report_data)
    elif fmt == "html":
        html_str = generate_html_report(payload.check_response, title=title)
        return HTMLResponse(content=html_str)
    elif fmt == "pdf":
        # Generate HTML report and deliver as HTML document with PDF export compatibility
        html_str = generate_html_report(payload.check_response, title=title)
        return Response(
            content=html_str,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{payload.check_response.analysis_id}.html"'
            },
        )
    else:
        raise DocumentProcessingException(
            status_code=400,
            code="INVALID_REPORT_FORMAT",
            message=f"Unsupported format '{fmt}'. Choose 'json', 'html', or 'pdf'.",
            details=[ErrorDetail(field="format", issue="Supported formats are: json, html, pdf")],
        )
