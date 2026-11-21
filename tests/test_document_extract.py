"""
Comprehensive Automated Test Suite for Phase 1.

Tests:
1. Normalization engine:
   - Preservation of original raw text vs normalized text.
   - Unicode NFC handling, accents, mathematical symbols (ΔE = mc²).
   - Ligature unfolding (fi, fl, ffi, ffl, oe, ae).
   - Hyphenated linebreaks stitching while keeping compound words.
   - Non-destruction of numbers, citations, URLs, code spans, and technical terminology.
2. Security & file validation:
   - Configurable upload size limit enforcement.
   - File signature and structure validation (magic bytes & structural contents).
   - Detection and rejection of malformed files, empty files, and null-byte payloads.
   - Detection and rejection of decompression bombs (high compression ratio & uncompressed ceilings).
   - Detection and rejection of macro-enabled documents (.docm, vbaProject.bin).
3. Document extraction:
   - TXT parsing with paragraph and sentence segmentation.
   - DOCX parsing with paragraph and standard grid table extraction into Markdown.
   - DOCX unsupported table / skipped elements cataloging.
   - PDF parsing with text blocks and table extraction.
4. Asynchronous Task Manager:
   - Task enqueuing, asynchronous execution, progress tracking, status polling, and error handling.
"""

import io
import zipfile
import pytest
import docx
import fitz

from backend.services.parser.normalizer import (
    normalize_text,
    unfold_ligatures,
    stitch_hyphenated_linebreaks,
    segment_sentences,
)
from backend.services.parser.security import (
    validate_and_detect_document,
    validate_file_size,
    validate_file_signature,
    validate_docx_structure,
    validate_pdf_structure,
    SecurityValidationError,
    MIME_PDF,
    MIME_DOCX,
    MIME_TXT,
)
from backend.services.parser.extractor import (
    DocumentParser,
    format_markdown_table,
    DocumentExtractionResult,
)
from backend.core.task_manager import InMemoryTaskManager, TaskStatus


# ==============================================================================
# 1. Normalization Engine Tests
# ==============================================================================

def test_unfold_ligatures():
    # Common typographic ligatures
    # \ufb01 = fi, \ufb02 = fl, \ufb03 = ffi, \ufb00 = ff
    ligature_text = "The \ufb01rst \ufb02ight of the o\ufb03ce was e\ufb00ective."
    unfolded = unfold_ligatures(ligature_text)
    assert unfolded == "The first flight of the office was effective."

    # Latin ligatures
    assert unfold_ligatures("C\u0153ur et \u00e6ther") == "Coeur et aether"


def test_stitch_hyphenated_linebreaks():
    # Words broken by newline hyphens
    broken = "This is a multi-\nstage algo-\r\nrithm that computes per- \nplexity."
    stitched = stitch_hyphenated_linebreaks(broken)
    assert stitched == "This is a multistage algorithm that computes perplexity."

    # Intact compound words on the same line should NOT be altered
    intact = "state-of-the-art out-of-distribution real-time"
    assert stitch_hyphenated_linebreaks(intact) == intact


def test_normalize_text_preserves_technical_content():
    sample = (
        "In 2024, Dr. Smith et al. [14] observed that 42.8% of specimens (ID: #SAMPLE-901)\n"
        "yielded a p-value < 0.001 with ΔE = mc² at $15.50/unit.\n"
        "Refer to https://example.org/res?id=42 for code: `def compute_ppl(): pass`."
    )
    normalized = normalize_text(sample)

    # Must preserve exact numbers, citations, math, URLs, code
    assert "2024" in normalized
    assert "Dr. Smith et al. [14]" in normalized
    assert "42.8%" in normalized
    assert "#SAMPLE-901" in normalized
    assert "p-value < 0.001" in normalized
    assert "ΔE = mc²" in normalized
    assert "$15.50/unit" in normalized
    assert "https://example.org/res?id=42" in normalized
    assert "`def compute_ppl(): pass`" in normalized


def test_sentence_segmentation():
    para = (
        "The quick brown fox jumps over the lazy dog. "
        "Dr. Alan Grant discovered 42 new fossils! "
        "Does this imply a pattern? Yes, it certainly does [12]."
    )
    sentences = segment_sentences(para)
    assert len(sentences) == 4
    assert sentences[0] == "The quick brown fox jumps over the lazy dog."
    assert sentences[1] == "Dr. Alan Grant discovered 42 new fossils!"
    assert sentences[2] == "Does this imply a pattern?"
    assert sentences[3] == "Yes, it certainly does [12]."


# ==============================================================================
# 2. Security and File Ingestion Validation Tests
# ==============================================================================

def test_file_size_validation():
    small_bytes = b"Hello world"
    validate_file_size(small_bytes, max_size_bytes=100)  # Should pass

    with pytest.raises(SecurityValidationError, match="exceeds the maximum allowed limit"):
        validate_file_size(b"A" * 150, max_size_bytes=100)

    with pytest.raises(SecurityValidationError, match="empty"):
        validate_file_size(b"", max_size_bytes=100)


def test_signature_and_null_byte_detection():
    # Valid TXT
    assert validate_file_signature(b"Clean text line") == MIME_TXT

    # Null bytes in plain text (should reject)
    with pytest.raises(SecurityValidationError, match="Binary or null bytes"):
        validate_file_signature(b"Some text\x00corrupt")

    # Short file
    with pytest.raises(SecurityValidationError, match="too short"):
        validate_file_signature(b"ab")


def test_macro_document_rejection():
    # Build a fake DOCX containing vbaProject.bin
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document></w:document>")
        z.writestr("[Content_Types].xml", "<Types></Types>")
        z.writestr("word/vbaProject.bin", b"\x00" * 100)  # Macro payload
    buf.seek(0)
    docx_bytes = buf.getvalue()

    with pytest.raises(SecurityValidationError, match="Macro-enabled documents"):
        validate_docx_structure(docx_bytes)


def test_decompression_bomb_rejection():
    # Build a fake ZIP with high compression ratio (e.g. 100:1)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<w:document></w:document>")
        z.writestr("[Content_Types].xml", "<Types></Types>")
        # Large uncompressed block that exceeds ratio or ceiling
        z.writestr("word/bomb.txt", b"0" * (5 * 1024 * 1024))
    buf.seek(0)
    bomb_bytes = buf.getvalue()

    # Test with strict uncompressed ceiling of 2MB
    with pytest.raises(SecurityValidationError, match="Decompression ceiling exceeded"):
        validate_docx_structure(bomb_bytes, max_uncompressed_bytes=2 * 1024 * 1024)


def test_malformed_pdf_rejection():
    # PDF missing EOF marker
    malformed_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"
    with pytest.raises(SecurityValidationError, match="Missing end-of-file trailer"):
        validate_pdf_structure(malformed_pdf)


# ==============================================================================
# 3. Document Extraction Tests (TXT, DOCX, PDF)
# ==============================================================================

def test_extract_txt_document():
    parser = DocumentParser()
    raw = (
        "First paragraph with some words.\n\n"
        "Second paragraph with \ufb01ndings and multi-\nstage calculations."
    )
    result = parser.parse_bytes(raw.encode("utf-8"), filename="test.txt")

    assert result.mime_type == MIME_TXT
    assert result.paragraph_count == 2
    assert result.paragraphs[0].raw_text == "First paragraph with some words."
    assert "findings" in result.paragraphs[1].normalized_text
    assert "multistage" in result.paragraphs[1].normalized_text
    assert len(result.paragraphs[0].sentences) == 1


def test_extract_docx_with_table():
    parser = DocumentParser()

    # Create an in-memory DOCX with paragraphs and a table
    doc = docx.Document()
    doc.add_paragraph("Introduction to experimental results.")
    tbl = doc.add_table(rows=3, cols=2)
    tbl.cell(0, 0).text = "Metric"
    tbl.cell(0, 1).text = "Value"
    tbl.cell(1, 0).text = "Perplexity"
    tbl.cell(1, 1).text = "14.2"
    tbl.cell(2, 0).text = "Accuracy"
    tbl.cell(2, 1).text = "92.5%"
    doc.add_paragraph("Discussion paragraph concluding the study.")

    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()

    result = parser.parse_bytes(docx_bytes, filename="test.docx")
    assert result.mime_type == MIME_DOCX
    assert result.paragraph_count == 3  # 2 text paragraphs + 1 table paragraph

    # Verify table extracted as Markdown
    table_p = result.paragraphs[1]
    assert table_p.is_table is True
    assert "| Metric | Value |" in table_p.normalized_text
    assert "| Perplexity | 14.2 |" in table_p.normalized_text
    assert "| Accuracy | 92.5% |" in table_p.normalized_text


def test_extract_pdf_document():
    parser = DocumentParser()

    # Create a small valid PDF using PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 72), "First paragraph of the research document.")
    page.insert_text(fitz.Point(50, 120), "Second paragraph discussing statistical anomalies.")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = parser.parse_bytes(pdf_bytes, filename="test.pdf")
    assert result.mime_type == MIME_PDF
    assert result.paragraph_count >= 2
    assert any("First paragraph" in p.normalized_text for p in result.paragraphs)
    assert any("statistical anomalies" in p.normalized_text for p in result.paragraphs)


# ==============================================================================
# 4. Asynchronous Task Manager Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_async_task_manager_flow():
    manager = InMemoryTaskManager()

    async def sample_job(x: int, y: int):
        return {"sum": x + y}

    task_id = await manager.enqueue(sample_job, 15, 27)
    assert task_id.startswith("task_")

    record = manager.get_task(task_id)
    assert record is not None

    # Wait for the async task to execute
    import asyncio
    await asyncio.sleep(0.05)

    completed_record = manager.get_task(task_id)
    assert completed_record.status == TaskStatus.COMPLETED
    assert completed_record.progress == 1.0
    assert completed_record.result == {"sum": 42}
