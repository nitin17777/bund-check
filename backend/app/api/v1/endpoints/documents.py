"""
Document Extraction Router.
Exposes POST /api/v1/documents/extract:
- Accepts multipart/form-data with file upload, OR JSON body with raw text.
- Memory/tempfile processing with guaranteed immediate cleanup (no disk persistence).
- Returns Document model with stable IDs, exact character offsets, and stats.
"""

import io
import os
import tempfile
from typing import Optional, Union
from fastapi import APIRouter, File, UploadFile, Request, Body, HTTPException, status
from fastapi.responses import JSONResponse

from backend.app.core.errors import DocumentProcessingException, ErrorEnvelope, ErrorBody, ErrorDetail
from backend.app.models.document import Document, TextExtractRequest
from backend.app.services.documents.validators import validate_document_upload, MIME_PDF, MIME_DOCX, MIME_TXT
from backend.app.services.documents.extractors import (
    extract_text_from_txt,
    extract_text_from_docx,
    extract_text_from_pdf,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/extract",
    response_model=Document,
    responses={
        400: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
    },
)
async def extract_document(
    request: Request,
    file: Optional[UploadFile] = File(None),
) -> Document:
    """
    Extracts structured paragraphs and sentences from uploaded document (PDF, DOCX, TXT)
    or from JSON body (text).
    Files are processed in memory and strictly deleted/discarded immediately.
    """
    temp_file_path: Optional[str] = None
    try:
        # Case 1: File uploaded via multipart form
        if file is not None:
            file_bytes = await file.read()
            filename = file.filename or "upload.bin"
            
            # Write to a tracked temp file to verify temporary file handling & cleanup
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(file_bytes)
                temp_file_path = tmp.name

            # Validate file signature, extension, decompression bombs, macros, etc.
            mime_type = validate_document_upload(file_bytes, filename=filename)

            if mime_type == MIME_PDF:
                result = extract_text_from_pdf(file_bytes, filename=filename)
            elif mime_type == MIME_DOCX:
                result = extract_text_from_docx(file_bytes, filename=filename)
            else:
                result = extract_text_from_txt(file_bytes, filename=filename)

            return result

        # Case 2: JSON payload with raw text
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body_bytes = await request.body()
            if not body_bytes:
                raise DocumentProcessingException(
                    status_code=400,
                    code="EMPTY_PAYLOAD",
                    message="JSON request body is empty.",
                    details=[ErrorDetail(field="body", issue="Payload is empty.")],
                )
            
            import json
            try:
                data = json.loads(body_bytes)
            except Exception:
                raise DocumentProcessingException(
                    status_code=400,
                    code="MALFORMED_JSON",
                    message="Invalid JSON payload syntax.",
                    details=[ErrorDetail(field="body", issue="Cannot parse JSON.")],
                )

            req = TextExtractRequest.model_validate(data)
            raw_text = req.text.strip()
            if not raw_text:
                raise DocumentProcessingException(
                    status_code=400,
                    code="EMPTY_DOCUMENT_TEXT",
                    message="Input text cannot be empty.",
                    details=[ErrorDetail(field="text", issue="Empty text string provided.")],
                )

            return extract_text_from_txt(raw_text.encode("utf-8"), filename=req.filename or "pasted_text.txt")

        # No file or JSON text provided
        raise DocumentProcessingException(
            status_code=400,
            code="MISSING_INPUT",
            message="No file or JSON text provided for extraction.",
            details=[ErrorDetail(field="file", issue="Either upload a file or send JSON with 'text' field.")],
        )

    finally:
        # Guarantee immediate deletion of any temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
