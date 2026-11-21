# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-11-21 (Phase 1: Document Extraction & Normalization)
- `backend/services/parser/security.py`: Deep file validation module enforcing configurable size limits, magic bytes, decompression bomb defenses (ratio and uncompressed limits), macro-enabled document rejection (`.docm`, `vbaProject.bin`), and structural file checks.
- `backend/services/parser/normalizer.py`: Deterministic text normalization module preserving original raw text separately, handling Unicode NFC composition (preserving math superscripts like $E=mc^2$), unfolding typographic ligatures, stitching hyphenated linebreaks, and segmenting sentences while respecting common abbreviations (`Dr.`, `et al.`).
- `backend/services/parser/extractor.py`: Unified `DocumentParser` extracting TXT, DOCX (`python-docx`), and PDF (`PyMuPDF`) into structured `ParagraphModel` and `SentenceModel` objects; extracts standard grid tables to Markdown pipe-tables and logs unsupported complex tables or drawings in `unsupported_elements` metadata.
- `backend/core/task_manager.py`: In-memory `asyncio` task manager with clean abstraction interface (`TaskManagerBase`) for async job dispatch and status polling.
- `tests/test_document_extract.py`: 13 automated unit tests validating security rules, bomb/macro rejection, normalization preservation, PDF/DOCX/TXT parsing, table formatting, and async task execution (all 13 passing).

### Added - 2026-11-21 (Phase 0: Scaffolding)
- Repository initialization and directory scaffolding (`frontend/`, `backend/`, `ml/`, `tests/`, `datasets/`, `docs/`).
- `AGENTS.md`: Mandatory operational rules for AI assistants and contributors (context acquisition, no faked APIs/mocks, testing enforcement, hardware boundaries).
- `GEMINI.md`: Antigravity/Gemini execution guidance.
- `PROJECT_STATUS.md`: Initial project tracking matrix with phase roadmap and test log templates.
- `docs/ARCHITECTURE.md`: Complete system architecture specification, Mermaid component and data flow diagrams, provider abstraction, persistence policies, and security/privacy safeguards.
- `docs/AI_MODEL_DESIGN.md`: Deep detection methodology, multi-signal ensemble, calibration, abstain bands, evaluation metrics, writing improver design with protected span extraction, and post-rewrite verification engine.
- `docs/API_SPEC.md`: Exhaustive REST API specification with Pydantic v2 schemas and error envelopes for `/api/v1/...` endpoints.
- `docs/DEVELOPMENT_ROADMAP.md`: Phases 0 through 10 with technical milestones, dependency graph, and PostgreSQL DDL schema with retention/deletion rules.
- `.gitignore` for Python, Node.js, Next.js, PyTorch models, and datasets.

### Changed - 2026-11-21 (Feasibility Audit Revisions)
- Standardized detection terminology from authorship probability to `synthetic_pattern_confidence` across `ARCHITECTURE.md`, `AI_MODEL_DESIGN.md`, `API_SPEC.md`, and `DEVELOPMENT_ROADMAP.md`.
- Formulated safe hardware profile: dynamic VRAM/RAM measurement (no fixed 1.4GB assumption), GPU execution for DistilGPT-2 and DistilRoBERTa with CPU fallback, and CPU execution for Sentence-Transformers and NLI DeBERTa.
- Configured 3-tier classification bands (`HUMAN_TYPICAL`, `INCONCLUSIVE`, `SYNTHETIC_INDICATIVE`) with an initial configurable $[0.40, 0.60]$ abstain band and initial word length filters ($50$ min, $150$ low-reliability).
- Expanded benchmarking standards to require prompt-disjoint evaluation across In-distribution LLMs, Out-of-distribution unseen LLMs, Human-edited AI text, and Diverse human writing, prioritizing TPR at $1\%$ and $5\%$ FPR.
- Expanded deterministic span protection and verification diffs to cover numbers, dates, measurement units, negations, citations, and technical terms.
- Added asynchronous task dispatch (`202 Accepted` + `GET /api/v1/tasks/{task_id}`) for documents $\ge 1,000$ words or multi-page file uploads.
- Clarified document extraction contract: standard grid tables are extracted into Markdown pipe-tables; unsupported complex/nested structures are skipped and cataloged in `unsupported_elements` metadata.
