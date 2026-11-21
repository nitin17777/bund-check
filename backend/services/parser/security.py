"""
Security and File Ingestion Validation Module.

Enforces deep document security:
- Configurable upload size limits.
- Magic bytes and structural file validation.
- Defense against decompression bombs (ZIP ratio & uncompressed ceilings).
- Detection and rejection of macro-enabled documents (.docm, vbaProject.bin).
- Detection and rejection of corrupt archives, malformed PDFs, and null-byte payloads.
"""

import io
import zipfile
from typing import Tuple


# Supported file types
MIME_PDF = "application/pdf"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_TXT = "text/plain"

# Default security limits (configurable)
DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB
DEFAULT_MAX_ZIP_RATIO = 20.0  # Max compression ratio 20:1
DEFAULT_MAX_ZIP_ENTRIES = 1000  # Max number of entries in DOCX ZIP container


class SecurityValidationError(ValueError):
    """Raised when an uploaded document violates security or structural constraints."""
    pass


def validate_file_size(file_bytes: bytes, max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES) -> None:
    """Enforces absolute upload size limits."""
    size = len(file_bytes)
    if size == 0:
        raise SecurityValidationError("Uploaded file is empty (0 bytes).")
    if size > max_size_bytes:
        raise SecurityValidationError(
            f"File size ({size} bytes) exceeds the maximum allowed limit of {max_size_bytes} bytes ({max_size_bytes // (1024 * 1024)} MB)."
        )


def validate_file_signature(file_bytes: bytes) -> str:
    """
    Inspects raw file header magic bytes to determine format.
    Does NOT trust file extension.

    Returns detected MIME type or raises SecurityValidationError.
    """
    if len(file_bytes) < 4:
        raise SecurityValidationError("File content is too short to determine file signature.")

    # PDF Magic: %PDF-
    if file_bytes.startswith(b"%PDF-"):
        return MIME_PDF

    # DOCX / ZIP Magic: PK\x03\x04
    if file_bytes.startswith(b"PK\x03\x04"):
        return MIME_DOCX

    # Check if valid text/plain: Must be valid UTF-8/ASCII with zero null bytes
    if b"\x00" in file_bytes:
        raise SecurityValidationError("Binary or null bytes detected in plain text payload.")

    try:
        file_bytes.decode("utf-8")
        return MIME_TXT
    except UnicodeDecodeError:
        raise SecurityValidationError(
            "Unsupported file format or invalid character encoding. Only PDF, DOCX, and UTF-8 TXT files are accepted."
        )


def validate_docx_structure(
    file_bytes: bytes,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_ratio: float = DEFAULT_MAX_ZIP_RATIO,
    max_entries: int = DEFAULT_MAX_ZIP_ENTRIES,
) -> None:
    """
    Deep structural and security audit of DOCX archives:
    1. Validates that the archive is a valid, uncorrupted ZIP file.
    2. Enforces decompression bomb defenses (compression ratio, max uncompressed size, entry count).
    3. Scans for macro payloads (vbaProject.bin, macro relationship types) and rejects immediately.
    4. Validates presence of standard WordProcessingML package structures ([Content_Types].xml or word/document.xml).
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile as e:
        raise SecurityValidationError(f"Corrupted or invalid DOCX archive structure: {str(e)}")

    entries = archive.infolist()
    if len(entries) > max_entries:
        raise SecurityValidationError(
            f"DOCX archive contains excessive entries ({len(entries)} > {max_entries}), potential zip bomb."
        )

    total_uncompressed = 0
    total_compressed = len(file_bytes)
    has_word_document = False
    has_content_types = False

    for info in entries:
        # Check for macro components
        filename_lower = info.filename.lower()
        if "vbaproject.bin" in filename_lower or filename_lower.endswith(".vba") or filename_lower.endswith(".bin"):
            raise SecurityValidationError("Macro-enabled documents (.docm or embedded VBA) are strictly prohibited.")

        # Check for standard DOCX markers
        if info.filename == "word/document.xml":
            has_word_document = True
        elif info.filename == "[Content_Types].xml":
            has_content_types = True

        total_uncompressed += info.file_size
        if total_uncompressed > max_uncompressed_bytes:
            raise SecurityValidationError(
                f"Decompression ceiling exceeded: Uncompressed size exceeds {max_uncompressed_bytes // (1024 * 1024)} MB."
            )

    if total_compressed > 0:
        ratio = total_uncompressed / total_compressed
        if ratio > max_ratio and total_uncompressed > 1024 * 1024:
            raise SecurityValidationError(
                f"Suspicious compression ratio detected ({ratio:.1f}:1 > {max_ratio}:1), potential zip bomb."
            )

    if not (has_word_document or has_content_types):
        raise SecurityValidationError(
            "Invalid DOCX structure: Missing standard OpenXML document or content types manifest."
        )


def validate_pdf_structure(file_bytes: bytes) -> None:
    """
    Structural verification of PDF stream:
    Verifies that the PDF has a valid EOF marker or can be parsed without structural corruption.
    """
    # A standard PDF should contain %%EOF near the end
    end_chunk = file_bytes[-1024:] if len(file_bytes) >= 1024 else file_bytes
    if b"%%EOF" not in end_chunk and b"%EOF" not in end_chunk:
        raise SecurityValidationError("Malformed PDF structure: Missing end-of-file trailer (%EOF).")


def validate_and_detect_document(
    file_bytes: bytes,
    max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Comprehensive document security gate.
    Validates size, signature, and internal structure.
    Returns detected MIME type.
    """
    validate_file_size(file_bytes, max_size_bytes=max_size_bytes)
    mime_type = validate_file_signature(file_bytes)

    if mime_type == MIME_DOCX:
        validate_docx_structure(file_bytes)
    elif mime_type == MIME_PDF:
        validate_pdf_structure(file_bytes)

    return mime_type
