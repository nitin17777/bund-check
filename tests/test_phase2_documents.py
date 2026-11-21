"""
Integration and Unit Tests for Phase 2:
- Tests all fixtures from tests/fixtures/
- Tests character offsets round-tripping for highlighting.
- Tests TestClient HTTP extraction for multipart and JSON text.
- Tests validation coverage >= 90%.
- Verifies that no temporary files remain on disk after extraction.
"""

import os
import io
import glob
import tempfile
import pytest
import pymupdf as fitz
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.services.documents.validators import (
    validate_document_upload,
    validate_file_size,
    validate_extension_and_signature,
    validate_docx_deep,
    validate_pdf_deep,
)
from backend.app.services.documents.extractors import (
    extract_text_from_txt,
    extract_text_from_docx,
    extract_text_from_pdf,
)
from backend.app.services.documents.segmentation import (
    normalize_paragraph_text,
    segment_sentences_with_offsets,
    guess_language,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
client = TestClient(app)


# ==============================================================================
# 1. Fixture Tests & Validation
# ==============================================================================

def test_fixture_txt_multi_paragraph_and_offsets():
    path = os.path.join(FIXTURES_DIR, "sample_document.txt")
    with open(path, "rb") as f:
        content = f.read()

    doc = extract_text_from_txt(content, filename="sample_document.txt")
    assert doc.stats.paragraph_count >= 3
    assert doc.stats.word_count > 20
    assert doc.language == "en"

    # Assert offset round-tripping:
    # 1. Paragraph offsets into normalized_full_text
    full_text = doc.normalized_full_text
    for p in doc.paragraphs:
        assert full_text[p.start_char : p.end_char] == p.normalized_text
        
        # 2. Sentence offsets into normalized paragraph text
        for s in p.sentences:
            assert p.normalized_text[s.start_char : s.end_char] == s.text


def test_fixture_docx_headings_and_tables():
    path = os.path.join(FIXTURES_DIR, "sample_report.docx")
    with open(path, "rb") as f:
        content = f.read()

    doc = extract_text_from_docx(content, filename="sample_report.docx")
    assert doc.stats.paragraph_count >= 4
    
    # Check heading detection
    headings = [p for p in doc.paragraphs if p.is_heading]
    assert len(headings) >= 2
    assert headings[0].heading_level == 1
    assert "Experimental Analysis Report" in headings[0].normalized_text

    # Check table detection
    tables = [p for p in doc.paragraphs if p.is_table]
    assert len(tables) >= 1
    assert "| Model | Accuracy |" in tables[0].normalized_text
    assert "| DistilRoBERTa | 94.2% |" in tables[0].normalized_text


def test_fixture_valid_pdf():
    path = os.path.join(FIXTURES_DIR, "valid_research.pdf")
    with open(path, "rb") as f:
        content = f.read()

    doc = extract_text_from_pdf(content, filename="valid_research.pdf")
    assert doc.stats.page_count == 1
    assert doc.stats.paragraph_count >= 1
    assert "Standard research paper" in doc.normalized_full_text


def test_fixture_empty_file_rejection():
    path = os.path.join(FIXTURES_DIR, "empty.txt")
    with open(path, "rb") as f:
        content = f.read()

    with pytest.raises(DocumentProcessingException) as exc_info:
        validate_document_upload(content, filename="empty.txt")
    assert exc_info.value.code == "FILE_EMPTY"


def test_fixture_oversized_file_rejection():
    path = os.path.join(FIXTURES_DIR, "oversized.txt")
    with open(path, "rb") as f:
        content = f.read()

    with pytest.raises(DocumentProcessingException) as exc_info:
        validate_document_upload(content, filename="oversized.txt")
    assert exc_info.value.code == "PAYLOAD_TOO_LARGE"


def test_fixture_spoofed_extension_rejection():
    # Plain text file named as .pdf
    path = os.path.join(FIXTURES_DIR, "spoofed_text_as_pdf.pdf")
    with open(path, "rb") as f:
        content = f.read()

    with pytest.raises(DocumentProcessingException) as exc_info:
        validate_document_upload(content, filename="spoofed_text_as_pdf.pdf")
    assert exc_info.value.code == "EXTENSION_SIGNATURE_MISMATCH"


def test_fixture_spoofed_docx_rejection():
    # Plain text file named as .docx
    path = os.path.join(FIXTURES_DIR, "spoofed_docx.docx")
    with open(path, "rb") as f:
        content = f.read()

    with pytest.raises(DocumentProcessingException) as exc_info:
        validate_document_upload(content, filename="spoofed_docx.docx")
    assert exc_info.value.code == "EXTENSION_SIGNATURE_MISMATCH"


def test_fixture_encrypted_pdf_rejection():
    path = os.path.join(FIXTURES_DIR, "encrypted.pdf")
    with open(path, "rb") as f:
        content = f.read()

    with pytest.raises(DocumentProcessingException) as exc_info:
        validate_document_upload(content, filename="encrypted.pdf")
    assert exc_info.value.code == "ENCRYPTED_FILE_NOT_SUPPORTED"


def test_fixture_scanned_pdf_rejection():
    path = os.path.join(FIXTURES_DIR, "scanned_image_only.pdf")
    with open(path, "rb") as f:
        content = f.read()

    # Pass validation, but extractor detects zero text with raster image
    with pytest.raises(DocumentProcessingException) as exc_info:
        extract_text_from_pdf(content, filename="scanned_image_only.pdf")
    assert exc_info.value.code == "SCANNED_PDF_OCR_NOT_SUPPORTED"


def test_fixture_zip_bomb_docx_rejection():
    path = os.path.join(FIXTURES_DIR, "zip_bomb.docx")
    with open(path, "rb") as f:
        content = f.read()

    with pytest.raises(DocumentProcessingException) as exc_info:
        validate_document_upload(content, filename="zip_bomb.docx")
    assert exc_info.value.code == "ZIP_BOMB_DETECTED"


# ==============================================================================
# 2. HTTP Endpoint Tests (FastAPI TestClient)
# ==============================================================================

def test_api_extract_endpoint_multipart_txt():
    path = os.path.join(FIXTURES_DIR, "sample_document.txt")
    with open(path, "rb") as f:
        response = client.post(
            "/api/v1/documents/extract",
            files={"file": ("sample_document.txt", f, "text/plain")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["mime_type"] == "text/plain"
    assert data["stats"]["paragraph_count"] >= 3
    assert len(data["paragraphs"]) >= 3
    
    # Assert offsets round-trip in API response
    full = data["normalized_full_text"]
    for p in data["paragraphs"]:
        assert full[p["start_char"] : p["end_char"]] == p["normalized_text"]
        for s in p["sentences"]:
            assert p["normalized_text"][s["start_char"] : s["end_char"]] == s["text"]


def test_api_extract_endpoint_multipart_docx():
    path = os.path.join(FIXTURES_DIR, "sample_report.docx")
    with open(path, "rb") as f:
        response = client.post(
            "/api/v1/documents/extract",
            files={"file": ("sample_report.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["paragraph_count"] >= 4


def test_api_extract_endpoint_json_text():
    payload = {
        "text": "This is raw pasted text.\n\nSecond paragraph with Dr. Smith et al. [14].",
        "filename": "pasted.txt",
    }
    response = client.post(
        "/api/v1/documents/extract",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["paragraph_count"] == 2
    assert "Dr. Smith et al. [14]" in data["paragraphs"][1]["normalized_text"]


def test_api_extract_endpoint_error_handling_rfc7807():
    # Empty file
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400
    err = response.json()["error"]
    assert err["code"] == "FILE_EMPTY"
    assert "empty" in err["message"].lower()

    # Oversized file
    oversized = b"X" * (10 * 1024 * 1024 + 100)
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("oversized.txt", oversized, "text/plain")},
    )
    assert response.status_code == 413
    err = response.json()["error"]
    assert err["code"] == "PAYLOAD_TOO_LARGE"


def test_no_temporary_files_left_behind():
    # List temp dir files before and after
    temp_dir = tempfile.gettempdir()
    initial_files = set(os.listdir(temp_dir))

    # Run upload
    path = os.path.join(FIXTURES_DIR, "sample_document.txt")
    with open(path, "rb") as f:
        response = client.post(
            "/api/v1/documents/extract",
            files={"file": ("sample_document.txt", f, "text/plain")},
        )
    assert response.status_code == 200

    after_files = set(os.listdir(temp_dir))
    # No new temp file should remain
    new_files = after_files - initial_files
    assert len(new_files) == 0


def test_language_detection_warning():
    # Russian Cyrillic text
    russian_text = "Это русский текст для проверки языкового детектора системы анализа текста."
    lang, warn = guess_language(russian_text)
    assert warn is not None
    assert "non-English" in warn


# ==============================================================================
# 3. Additional Validator Unit Tests for >= 90% Coverage
# ==============================================================================

def test_validator_short_bytes():
    with pytest.raises(DocumentProcessingException) as exc:
        validate_document_upload(b"ab")
    assert exc.value.code == "INVALID_SIGNATURE"


def test_validator_null_bytes_in_text():
    with pytest.raises(DocumentProcessingException) as exc:
        validate_document_upload(b"text\x00with null")
    assert exc.value.code == "CORRUPTED_OR_BINARY_FILE"


def test_validator_unsupported_extension():
    with pytest.raises(DocumentProcessingException) as exc:
        validate_document_upload(b"Hello world", filename="data.csv")
    assert exc.value.code == "UNSUPPORTED_EXTENSION"


def test_validator_corrupted_docx_zip():
    with pytest.raises(DocumentProcessingException) as exc:
        validate_docx_deep(b"PK\x03\x04corrupted_payload")
    assert exc.value.code == "CORRUPTED_DOCX"


def test_validator_docx_encrypted_entry():
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document></w:document>")
        z.writestr("[Content_Types].xml", "<Types></Types>")
        z.writestr("word/secret.xml", b"secret data")
    
    # Manually flip encrypted bit in central directory record
    raw = bytearray(buf.getvalue())
    cd_marker = b"PK\x01\x02"
    idx = raw.find(cd_marker)
    while idx != -1:
        raw[idx + 8] = 0x01  # Set bit 0 (encrypted)
        idx = raw.find(cd_marker, idx + 4)
    
    with pytest.raises(DocumentProcessingException) as exc:
        validate_docx_deep(bytes(raw))
    assert exc.value.code == "ENCRYPTED_FILE_NOT_SUPPORTED"


def test_validator_docx_missing_manifest():
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("some_other_folder/file.xml", "<root></root>")
    with pytest.raises(DocumentProcessingException) as exc:
        validate_docx_deep(buf.getvalue())
    assert exc.value.code == "INVALID_DOCX_STRUCTURE"


def test_validator_docx_uncompressed_ceiling():
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<w:document></w:document>")
        z.writestr("[Content_Types].xml", "<Types></Types>")
        # Create uncompressed size exceeding limit (50 MB)
        z.writestr("word/huge.dat", b"A" * (51 * 1024 * 1024))
    
    with pytest.raises(DocumentProcessingException) as exc:
        validate_docx_deep(buf.getvalue())
    assert exc.value.code == "ZIP_BOMB_DETECTED"


def test_validator_pdf_missing_eof():
    with pytest.raises(DocumentProcessingException) as exc:
        validate_pdf_deep(b"%PDF-1.4\nSome broken stream without EOF")
    assert exc.value.code == "CORRUPTED_PDF"


def test_validator_pdf_page_limit_exceeded():
    doc = fitz.open()
    # Add pages exceeding limit
    for _ in range(settings.MAX_PDF_PAGES + 2):
        doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    with pytest.raises(DocumentProcessingException) as exc:
        validate_pdf_deep(pdf_bytes)
    assert exc.value.code == "PDF_PAGE_LIMIT_EXCEEDED"
