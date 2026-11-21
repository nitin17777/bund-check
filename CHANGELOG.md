# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-11-21 (Phase 2: Backend Foundation and Document Processing)
- `backend/app/services/documents/validators.py`: Comprehensive security validators enforcing size limits, extension and magic-byte consistency, DOCX ZIP decompression ratio and entry count defenses, rejection of macro-enabled files (`.docm`, `vbaProject.bin`), password-protected DOCX/PDF rejection, and PDF page count limits. (96% test coverage).
- `backend/app/services/documents/segmentation.py`: Segmentation engine providing paragraph normalization, sentence boundary detection robust to abbreviations, citations (`[14]`, `(Smith et al., 2020)`), and bullet lists, with stable ID generation and exact character offset calculation.
- `backend/app/services/documents/extractors.py`: Document extractors for PDF (PyMuPDF with scanned/image-only PDF detection), DOCX (python-docx with heading levels, paragraphs, tables), and TXT (charset-normalizer encoding detection).
- `backend/app/models/document.py`: Pydantic models for Document, Paragraph, Sentence, DocumentStats, and UnsupportedElement with stable IDs and start/end character offsets.
- `backend/app/api/v1/endpoints/documents.py`: `POST /api/v1/documents/extract` endpoint supporting multipart file uploads and JSON pasted text with immediate cleanup of temp files.
- `backend/app/main.py`: FastAPI entrypoint with RFC 7807 problem details error handling.
- `tests/fixtures/*`: 11 real test fixtures covering multi-paragraph text, DOCX tables/headings, ligatures, empty files, spoofed extensions, oversized files, encrypted PDFs, scanned PDFs, and zip-bombs.
- `tests/test_phase2_documents.py`: 25 automated unit and integration tests verifying all fixtures, offset round-trips, HTTP TestClient requests, tempfile cleanup, and validator edge cases.

### Verified & Hardened - 2026-11-21 (Phase 1 Final Verification)
- Expanded test suite to 20 automated tests, covering ZIP entry overflow attacks, corrupt DOCX ZIP structures, missing OpenXML manifests, non-UTF8 rejection, complex merged-cell table detection, async task failure states, and raw text immutability.
- Eliminated pytest-asyncio and PyMuPDF deprecation warnings (`pyproject.toml` configuration and `pymupdf` import modernization).
- Enhanced merged-cell table detection in DOCX parser (`backend/services/parser/extractor.py`) to safely catalog merged grids in `unsupported_elements` metadata.
- Reconciled phase milestones across `DEVELOPMENT_ROADMAP.md` and `PROJECT_STATUS.md`.

### Added - 2026-11-21 (Phase 1: Document Extraction & Normalization)
- `backend/services/parser/security.py`: File validation module enforcing configurable size limits, magic bytes, decompression bomb defenses, and macro rejection.
- `backend/services/parser/normalizer.py`: Text normalization module preserving raw text, handling Unicode NFC composition, unfolding typographic ligatures, stitching hyphenated linebreaks, and segmenting sentences.
- `backend/services/parser/extractor.py`: Unified `DocumentParser` extracting TXT, DOCX, and PDF into structured models and markdown tables.
- `backend/core/task_manager.py`: In-memory `asyncio` task manager with clean abstraction interface (`TaskManagerBase`).

### Added - 2026-11-21 (Phase 0: Scaffolding)
- Repository initialization and directory scaffolding (`frontend/`, `backend/`, `ml/`, `tests/`, `datasets/`, `docs/`).
- `AGENTS.md`, `GEMINI.md`, `PROJECT_STATUS.md`, `docs/ARCHITECTURE.md`, `docs/AI_MODEL_DESIGN.md`, `docs/API_SPEC.md`, `docs/DEVELOPMENT_ROADMAP.md`.
