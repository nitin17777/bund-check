# PROJECT_STATUS.md — Project Execution & Verification Tracker

## Active Project Phase
**Current Phase**: Phase 2 — Backend Foundation and Document Processing Engine  
**Status**: Completed and Rigorously Verified (45/45 Tests Passing, Validators Coverage 96%)

---

## Phase Roadmap Status

| Phase | Description | Status | Completed Date |
|---|---|---|---|
| **Phase 0** | Project Scaffolding, Architecture, Specs & Environment Setup | **Completed** | 2026-11-21 |
| **Phase 1** | Document Extraction, Normalization & Table Ingestion Pipeline | **Completed** | 2026-11-21 |
| **Phase 2** | Backend Foundation, Security Validators & Document Extract API | **Completed** | 2026-11-21 |
| **Phase 3** | Statistical & Stylometric Feature Extraction Engine (Pure CPU) | Pending | — |
| **Phase 4** | Transformer Classifier, Perplexity Signal & Model Ensemble (GPU Safe) | Pending | — |
| **Phase 5** | Calibration, Abstain Band, Sentence Attribution & Cross-Generator Benchmark | Pending | — |
| **Phase 6** | Writing Improver Engine & Expanded Protected Span Extraction | Pending | — |
| **Phase 7** | Multi-Stage Post-Rewrite Verification Layer (Pure CPU) | Pending | — |
| **Phase 8** | FastAPI Core Services, Async Task Dispatch & REST API Endpoints | Pending | — |
| **Phase 9** | Next.js Frontend — Review Dashboard & Interactive Diff View | Pending | — |
| **Phase 10**| Docker Deployment, Benchmarking & Documentation Finalization | Pending | — |

---

## Session Log: Phase 2 Implementation & Verification

### Completed Tasks
1. **Document Security & Validation (`backend/app/services/documents/validators.py`)**:
   - Enforced combined file extension AND magic-byte verification (rejecting spoofed extensions).
   - Enforced upload size limits from Pydantic settings.
   - Deep DOCX inspection: entry count ceilings, decompression bomb uncompressed-to-compressed ratio checks, macro-enabled file rejection (`.docm`, `vbaProject.bin`), and password-encrypted ZIP rejection.
   - Deep PDF inspection: EOF validation, page-count limit enforcement (default 200 pages), and encrypted PDF rejection.
   - Plain text validation: detection and rejection of null-byte or binary control payloads.
   - **Validator test coverage achieved: 96%** (exceeding the >= 90% requirement).
2. **Text Extraction & Ingestion Engine (`backend/app/services/documents/extractors.py`)**:
   - PyMuPDF extraction for PDF: detects scanned/image-only PDFs (raises `SCANNED_PDF_OCR_NOT_SUPPORTED`), extracts text blocks and standard tables.
   - python-docx extraction for DOCX: extracts headings with heading level metadata (`heading_level: 1..6`), paragraphs, and standard grid tables.
   - Plain-text extraction: automated encoding detection via `charset-normalizer` with fallback to UTF-8.
   - Empty extracted text detection across all formats (raises `EMPTY_DOCUMENT_TEXT`).
3. **Segmentation & Stable Offsets Engine (`backend/app/services/documents/segmentation.py`)**:
   - Segmented paragraphs and sentences with stable IDs (`p0`, `p0_s0`).
   - Sentence boundary splitting robust to abbreviations (`Dr.`, `et al.`), citations (`[14]`, `(Smith et al., 2020)`), decimals (`42.8%`), and bullet lists.
   - Character offset tracking: exact start and end offsets into normalized text for both paragraphs and sentences.
   - **Exact character offset round-trip verified**: `normalized_full_text[p.start_char:p.end_char] == p.normalized_text` and `p.normalized_text[s.start_char:s.end_char] == s.text`.
   - Heuristic language identification (warns user if text is non-English).
4. **FastAPI Endpoint (`POST /api/v1/documents/extract`)**:
   - Accepts multipart/form-data for files or JSON payload with `text`.
   - In-memory / temporary file processing with guaranteed immediate deletion upon response delivery (verified 0 temp files left behind).
   - Structured RFC 7807 problem details error envelopes (`ErrorEnvelope`).
   - Zero database persistence; zero LLM/detector calls.
5. **Testing & Real Verification**:
   - Generated 11 real document fixtures in `tests/fixtures/`: multi-paragraph text, table DOCX, unicode ligatures, empty file, spoofed extension, oversized file, encrypted PDF, scanned-style PDF with no text, and zip-bomb DOCX.
   - Automated tests executed via `pytest`: **45/45 passing across all suites**.
   - Verified live server execution via FastAPI `TestClient` AND actual curl/PowerShell HTTP uploads against uvicorn on port 8000.

### Modified / Created Files
- `backend/app/__init__.py`
- `backend/app/core/config.py` (Pydantic settings with limits)
- `backend/app/core/errors.py` (RFC 7807 error envelopes and exception types)
- `backend/app/models/document.py` (Pydantic document/paragraph/sentence models with stable IDs & offsets)
- `backend/app/services/documents/validators.py` (Security validator with 96% coverage)
- `backend/app/services/documents/segmentation.py` (Segmentation with exact offset round-tripping)
- `backend/app/services/documents/extractors.py` (TXT/DOCX/PDF extractors with scanned PDF detection)
- `backend/app/api/v1/endpoints/documents.py` (POST /api/v1/documents/extract endpoint)
- `backend/app/main.py` (FastAPI application entry point)
- `tests/create_fixtures.py` (Fixture generator script)
- `tests/fixtures/*` (11 real test files)
- `tests/test_phase2_documents.py` (25 tests covering fixtures, offsets, endpoints, cleanup, and validators)
- `PROJECT_STATUS.md` (Updated phase tracking and test results)
- `CHANGELOG.md` (Updated release log)

### Test Commands and ACTUAL Results
1. **Full Test Suite & Coverage**:
   - Command:
     ```powershell
     .\.venv\Scripts\python -m pytest -v --cov=backend.app.services.documents.validators --cov-report=term-missing
     ```
   - Actual Output:
     ```
     ======================== 45 passed, 1 warning in 3.42s ========================
     Coverage for backend.app.services.documents.validators: 96% (93 statements, 4 missed)
     ```
2. **Live Server Real HTTP & cURL Verification**:
   - Command:
     ```powershell
     Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/extract" -Method Post -ContentType "application/json" -Body '{"text": "Pasted text test.\n\nSecond paragraph."}'
     curl.exe -s -F "file=@tests/fixtures/sample_document.txt" http://127.0.0.1:8000/api/v1/documents/extract
     ```
   - Result:
     `HTTP JSON Response: words=5, paras=2`
     `CURL Output: {"document_id":"doc_...","filename":"sample_document.txt","mime_type":"text/plain",...}`

### Remaining Known Limitations
- OCR for scanned/image-only PDFs is intentionally not supported in Phase 2; the endpoint returns a clear 422 error code `SCANNED_PDF_OCR_NOT_SUPPORTED`.
- Temporary files created during extraction are guaranteed removed immediately; no server persistence exists by design.

### Outstanding Tasks for Next Phase
- **Phase 3 Initiation**: Implement pure-CPU Statistical & Stylometric Feature Extractor (`ml/features/stylometry.py`) for TTR, Hapax Legomena, POS entropy, sentence length variance, and negation density.
