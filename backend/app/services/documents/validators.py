"""
Document Security & Validation Module.
Enforces:
- File size checking from configuration.
- Combined extension AND magic-byte verification (rejects spoofed extensions).
- DOCX deep inspection: ZIP entry count, decompression uncompressed-to-compressed ratio ceiling,
  rejection of macro-enabled files (.docm, vbaProject.bin), encrypted ZIP archives.
- PDF inspection: EOF check, encrypted PDF rejection, page-count limit enforcement.
- Plain-text validation: null-byte rejection.
"""

import io
import zipfile
from typing import Optional, Tuple
import pymupdf as fitz

from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException, ErrorDetail

MIME_PDF = "application/pdf"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_TXT = "text/plain"

ALLOWED_EXTENSIONS = {
    ".pdf": MIME_PDF,
    ".docx": MIME_DOCX,
    ".txt": MIME_TXT,
}


def validate_file_size(file_bytes: bytes, max_size_bytes: Optional[int] = None) -> None:
    max_size = max_size_bytes or settings.MAX_FILE_SIZE_BYTES
    size = len(file_bytes)
    if size == 0:
        raise DocumentProcessingException(
            status_code=400,
            code="FILE_EMPTY",
            message="Uploaded file is empty (0 bytes).",
            details=[ErrorDetail(field="file", issue="File contains 0 bytes.")],
        )
    if size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise DocumentProcessingException(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message=f"File size ({size} bytes) exceeds maximum allowed limit of {max_mb} MB.",
            details=[ErrorDetail(field="file", issue=f"Max size is {max_size} bytes; received {size} bytes.")],
        )


def detect_magic_signature(file_bytes: bytes) -> str:
    if len(file_bytes) < 4:
        raise DocumentProcessingException(
            status_code=400,
            code="INVALID_SIGNATURE",
            message="File content is too short to determine valid format.",
            details=[ErrorDetail(field="file", issue="Fewer than 4 bytes in file.")],
        )

    if file_bytes.startswith(b"%PDF-"):
        return MIME_PDF

    if file_bytes.startswith(b"PK\x03\x04"):
        return MIME_DOCX

    if b"\x00" in file_bytes:
        raise DocumentProcessingException(
            status_code=422,
            code="CORRUPTED_OR_BINARY_FILE",
            message="Binary control or null bytes detected in plain text payload.",
            details=[ErrorDetail(field="file", issue="Contains null bytes (0x00).")],
        )

    return MIME_TXT


def validate_extension_and_signature(filename: Optional[str], file_bytes: bytes) -> str:
    detected_mime = detect_magic_signature(file_bytes)

    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext in ALLOWED_EXTENSIONS:
            expected_mime = ALLOWED_EXTENSIONS[ext]
            if expected_mime != detected_mime:
                raise DocumentProcessingException(
                    status_code=422,
                    code="EXTENSION_SIGNATURE_MISMATCH",
                    message=f"File extension '{ext}' does not match detected content format '{detected_mime}'.",
                    details=[ErrorDetail(field="filename", issue=f"Extension '{ext}' mismatches magic '{detected_mime}'.")],
                )
        else:
            raise DocumentProcessingException(
                status_code=422,
                code="UNSUPPORTED_EXTENSION",
                message=f"File extension '{ext}' is not supported. Supported extensions: .pdf, .docx, .txt.",
                details=[ErrorDetail(field="filename", issue=f"Extension '{ext}' not allowed.")],
            )

    return detected_mime


def validate_docx_deep(file_bytes: bytes) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile as e:
        raise DocumentProcessingException(
            status_code=422,
            code="CORRUPTED_DOCX",
            message=f"Corrupted or invalid DOCX archive structure: {str(e)}",
            details=[ErrorDetail(field="file", issue="Corrupted ZIP stream.")],
        )

    entries = archive.infolist()
    if len(entries) > settings.MAX_ZIP_ENTRIES:
        raise DocumentProcessingException(
            status_code=422,
            code="ZIP_BOMB_DETECTED",
            message=f"DOCX archive contains excessive entries ({len(entries)} > {settings.MAX_ZIP_ENTRIES}).",
            details=[ErrorDetail(field="file", issue="Entry count ceiling exceeded.")],
        )

    total_uncompressed = 0
    total_compressed = len(file_bytes)
    has_word_document = False
    has_content_types = False

    for info in entries:
        # Check for encrypted ZIP entry
        if info.flag_bits & 0x1:
            raise DocumentProcessingException(
                status_code=422,
                code="ENCRYPTED_FILE_NOT_SUPPORTED",
                message="Password-protected or encrypted DOCX archives are not supported.",
                details=[ErrorDetail(field="file", issue="Encrypted zip entry detected.")],
            )

        filename_lower = info.filename.lower()
        if "vbaproject.bin" in filename_lower or filename_lower.endswith(".vba") or filename_lower.endswith(".bin"):
            raise DocumentProcessingException(
                status_code=422,
                code="MACRO_DOCUMENTS_PROHIBITED",
                message="Macro-enabled documents (.docm or embedded VBA) are strictly prohibited.",
                details=[ErrorDetail(field="file", issue=f"Found macro component: {info.filename}")],
            )

        if info.filename == "word/document.xml":
            has_word_document = True
        elif info.filename == "[Content_Types].xml":
            has_content_types = True

        total_uncompressed += info.file_size
        if total_uncompressed > settings.MAX_UNCOMPRESSED_DOCX_BYTES:
            max_mb = settings.MAX_UNCOMPRESSED_DOCX_BYTES // (1024 * 1024)
            raise DocumentProcessingException(
                status_code=422,
                code="ZIP_BOMB_DETECTED",
                message=f"Decompression ceiling exceeded: Uncompressed size exceeds {max_mb} MB.",
                details=[ErrorDetail(field="file", issue="Uncompressed size limit reached.")],
            )

    if total_compressed > 0 and total_uncompressed > 1024 * 1024:
        ratio = total_uncompressed / total_compressed
        if ratio > settings.MAX_ZIP_RATIO:
            raise DocumentProcessingException(
                status_code=422,
                code="ZIP_BOMB_DETECTED",
                message=f"Suspicious compression ratio ({ratio:.1f}:1 > {settings.MAX_ZIP_RATIO}:1).",
                details=[ErrorDetail(field="file", issue="Compression ratio exceeds safety ceiling.")],
            )

    if not (has_word_document or has_content_types):
        raise DocumentProcessingException(
            status_code=422,
            code="INVALID_DOCX_STRUCTURE",
            message="Invalid DOCX structure: Missing standard OpenXML document or content types manifest.",
            details=[ErrorDetail(field="file", issue="Missing word/document.xml or [Content_Types].xml.")],
        )


def validate_pdf_deep(file_bytes: bytes) -> None:
    end_chunk = file_bytes[-1024:] if len(file_bytes) >= 1024 else file_bytes
    if b"%%EOF" not in end_chunk and b"%EOF" not in end_chunk:
        raise DocumentProcessingException(
            status_code=422,
            code="CORRUPTED_PDF",
            message="Malformed PDF structure: Missing end-of-file trailer (%EOF).",
            details=[ErrorDetail(field="file", issue="Missing %%EOF marker.")],
        )

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise DocumentProcessingException(
            status_code=422,
            code="CORRUPTED_PDF",
            message=f"Failed to parse PDF document structure: {str(e)}",
            details=[ErrorDetail(field="file", issue="PDF structure unparseable.")],
        )

    if doc.is_encrypted:
        doc.close()
        raise DocumentProcessingException(
            status_code=422,
            code="ENCRYPTED_FILE_NOT_SUPPORTED",
            message="Encrypted or password-protected PDF files are not supported.",
            details=[ErrorDetail(field="file", issue="PDF is encrypted.")],
        )

    page_count = len(doc)
    doc.close()

    if page_count > settings.MAX_PDF_PAGES:
        raise DocumentProcessingException(
            status_code=422,
            code="PDF_PAGE_LIMIT_EXCEEDED",
            message=f"PDF page count ({page_count}) exceeds limit of {settings.MAX_PDF_PAGES} pages.",
            details=[ErrorDetail(field="file", issue=f"Max pages allowed is {settings.MAX_PDF_PAGES}.")],
        )


def validate_document_upload(file_bytes: bytes, filename: Optional[str] = None) -> str:
    validate_file_size(file_bytes)
    mime_type = validate_extension_and_signature(filename, file_bytes)

    if mime_type == MIME_DOCX:
        validate_docx_deep(file_bytes)
    elif mime_type == MIME_PDF:
        validate_pdf_deep(file_bytes)

    return mime_type
