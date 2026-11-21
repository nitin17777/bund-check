# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Verified & Hardened - 2026-11-21 (Phase 1 Final Verification)
- Expanded test suite from 13 to 20 automated tests, covering ZIP entry overflow attacks, corrupt DOCX ZIP structures, missing OpenXML manifests, non-UTF8 rejection, complex merged-cell table detection, async task failure states, and raw text immutability.
- Eliminated pytest-asyncio and PyMuPDF deprecation warnings (`pyproject.toml` configuration and `pymupdf` import modernization).
- Enhanced merged-cell table detection in DOCX parser (`backend/services/parser/extractor.py`) to safely catalog merged grids in `unsupported_elements` metadata.
- Reconciled phase milestones across `DEVELOPMENT_ROADMAP.md` and `PROJECT_STATUS.md`.

### Added - 2026-11-21 (Phase 1: Document Extraction & Normalization)
- `backend/services/parser/security.py`: Deep file validation module enforcing configurable size limits, magic bytes, decompression bomb defenses (ratio and uncompressed limits), macro-enabled document rejection (`.docm`, `vbaProject.bin`), and structural file checks.
- `backend/services/parser/normalizer.py`: Deterministic text normalization module preserving original raw text separately, handling Unicode NFC composition (preserving math superscripts like $E=mc^2$), unfolding typographic ligatures, stitching hyphenated linebreaks, and segmenting sentences while respecting common abbreviations (`Dr.`, `et al.`).
- `backend/services/parser/extractor.py`: Unified `DocumentParser` extracting TXT, DOCX (`python-docx`), and PDF (`PyMuPDF`) into structured `ParagraphModel` and `SentenceModel` objects; extracts standard grid tables to Markdown pipe-tables and logs unsupported complex tables or drawings in `unsupported_elements` metadata.
- `backend/core/task_manager.py`: In-memory `asyncio` task manager with clean abstraction interface (`TaskManagerBase`) for async job dispatch and status polling.
- `tests/test_document_extract.py`: Automated unit tests validating security rules, bomb/macro rejection, normalization preservation, PDF/DOCX/TXT parsing, table formatting, and async task execution.

### Added - 2026-11-21 (Phase 0: Scaffolding)
- Repository initialization and directory scaffolding (`frontend/`, `backend/`, `ml/`, `tests/`, `datasets/`, `docs/`).
- `AGENTS.md`: Mandatory operational rules for AI assistants and contributors.
- `GEMINI.md`: Antigravity/Gemini execution guidance.
- `PROJECT_STATUS.md`: Initial project tracking matrix with phase roadmap and test log templates.
- `docs/ARCHITECTURE.md`: Complete system architecture specification.
- `docs/AI_MODEL_DESIGN.md`: Deep detection methodology and verification engine design.
- `docs/API_SPEC.md`: Exhaustive REST API specification with Pydantic v2 schemas.
- `docs/DEVELOPMENT_ROADMAP.md`: Phases 0 through 10 with technical milestones and PostgreSQL DDL schema.
- `.gitignore` for Python, Node.js, Next.js, PyTorch models, and datasets.
