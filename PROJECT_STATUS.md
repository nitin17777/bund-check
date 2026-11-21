# PROJECT_STATUS.md — Project Execution & Verification Tracker

## Active Project Phase
**Current Phase**: Phase 1 — Document Extraction, Normalization & Table Ingestion Pipeline  
**Status**: Completed and Verified

---

## Phase Roadmap Status

| Phase | Description | Status | Completed Date |
|---|---|---|---|
| **Phase 0** | Project Scaffolding, Architecture, Specs & Environment Setup | **Completed** | 2026-11-21 |
| **Phase 1** | Document Extraction, Normalization & Table Ingestion Pipeline | **Completed** | 2026-11-21 |
| **Phase 2** | Statistical & Stylometric Feature Extraction Engine (Pure CPU) | Pending | — |
| **Phase 3** | Transformer Classifier, Perplexity Signal & Model Ensemble (GPU Safe) | Pending | — |
| **Phase 4** | Calibration, Abstain Band, Sentence Attribution & Cross-Generator Benchmark | Pending | — |
| **Phase 5** | Writing Improver Engine & Expanded Protected Span Extraction | Pending | — |
| **Phase 6** | Multi-Stage Post-Rewrite Verification Layer (Pure CPU) | Pending | — |
| **Phase 7** | FastAPI Core Services, Async Task Dispatch & REST API Endpoints | Pending | — |
| **Phase 8** | Next.js Frontend — Review Dashboard & Interactive Diff View | Pending | — |
| **Phase 9** | End-to-End Integration, Security Hardening & Rate Limiting | Pending | — |
| **Phase 10**| Docker Deployment, Benchmarking & Documentation Finalization | Pending | — |

---

## Session Log: Phase 1 Implementation & Verification

### Completed Tasks
1. **Document Security Ingestion (`backend/services/parser/security.py`)**:
   - Enforced configurable upload size limits (10MB default).
   - Validated magic bytes and internal structures for PDF (`%PDF-`, EOF trailer), DOCX (`PK\x03\x04`, `[Content_Types].xml`, `word/document.xml`), and TXT (UTF-8 encoding, null-byte rejection).
   - Implemented decompression bomb defense (20:1 compression ratio limit, 50MB uncompressed ceiling, 1,000 ZIP entry ceiling).
   - Implemented macro rejection (`.docm`, `vbaProject.bin`, `.vba` entries).
2. **Deterministic Text Normalization (`backend/services/parser/normalizer.py`)**:
   - Separated raw extracted text from normalized text.
   - Unicode NFC composition preserving mathematical superscripts ($E=mc^2$) and symbols without mutating technical terms or citations.
   - Typographic ligature unfolding (`fi`, `fl`, `ffi`, `ffl`, `oe`, `ae`).
   - Line-break hyphen stitching preserving valid intra-line compound words.
   - Sentence segmentation respecting known abbreviations (`Dr.`, `et al.`, `e.g.`, `vs.`).
3. **Document Parser & Table Ingestion (`backend/services/parser/extractor.py`)**:
   - Implemented unified `DocumentParser` for TXT, DOCX (`python-docx`), and PDF (`PyMuPDF`).
   - Standard grid tables extracted into clean Markdown pipe-tables.
   - Unsupported nested/merged table structures detected, skipped, and recorded in `unsupported_elements` metadata.
4. **Asynchronous In-Memory Task Manager (`backend/core/task_manager.py`)**:
   - Implemented thread-safe `InMemoryTaskManager` with task enqueuing, progress tracking, status polling, and result storage.
   - Explicitly documented MVP restart and task-loss limitations.
   - Cleanly decoupled via `TaskManagerBase` for zero-friction migration to persistent queues (Redis/Celery) in Phase 9.
5. **Comprehensive Automated Test Suite (`tests/test_document_extract.py`)**:
   - 13 comprehensive unit and integration tests covering normalization, security, ingestion attacks (bombs, macros, corrupt headers), PDF/DOCX/TXT extraction, and async task execution.

### Modified / Created Files
- `pyproject.toml` (Created Python package dependencies configuration)
- `backend/__init__.py`
- `backend/core/__init__.py`
- `backend/core/task_manager.py` (Async task manager implementation)
- `backend/services/__init__.py`
- `backend/services/parser/__init__.py`
- `backend/services/parser/normalizer.py` (Text normalizer)
- `backend/services/parser/security.py` (Security validator)
- `backend/services/parser/extractor.py` (Unified document parser)
- `tests/test_document_extract.py` (13 automated unit tests)
- `PROJECT_STATUS.md` (Updated phase tracking and test logs)
- `CHANGELOG.md` (Updated release history)

### Test Commands and ACTUAL Results
- **Command**:
  ```powershell
  .\.venv\Scripts\python -m pytest -v tests/test_document_extract.py
  ```
- **Actual Raw Output**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0 -- D:\bund-check\.venv\Scripts\python.exe
  cachedir: .pytest_cache
  rootdir: D:\bund-check
  configfile: pyproject.toml
  plugins: asyncio-1.5.0
  asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collecting ... collected 13 items

  tests/test_document_extract.py::test_unfold_ligatures PASSED             [  7%]
  tests/test_document_extract.py::test_stitch_hyphenated_linebreaks PASSED [ 15%]
  tests/test_document_extract.py::test_normalize_text_preserves_technical_content PASSED [ 23%]
  tests/test_document_extract.py::test_sentence_segmentation PASSED        [ 30%]
  tests/test_document_extract.py::test_file_size_validation PASSED         [ 38%]
  tests/test_document_extract.py::test_signature_and_null_byte_detection PASSED [ 46%]
  tests/test_document_extract.py::test_macro_document_rejection PASSED     [ 53%]
  tests/test_document_extract.py::test_decompression_bomb_rejection PASSED [ 61%]
  tests/test_document_extract.py::test_malformed_pdf_rejection PASSED      [ 69%]
  tests/test_document_extract.py::test_extract_txt_document PASSED         [ 76%]
  tests/test_document_extract.py::test_extract_docx_with_table PASSED      [ 84%]
  tests/test_document_extract.py::test_extract_pdf_document PASSED         [ 92%]
  tests/test_document_extract.py::test_async_task_manager_flow PASSED      [100%]

  ======================== 13 passed, 1 warning in 5.65s ========================
  ```

### Known Bugs / Technical Debt
- In Windows sandboxed subprocesses with Python 3.13, default IOCP (`ProactorEventLoop`) pipe operations require running outside the sandbox (`BypassSandbox: true`) for `asyncio` loop completion. This is documented and accounted for.

### Outstanding Tasks for Next Phase
- **Phase 2 Initiation**: Implement Statistical & Stylometric Feature Extraction Engine (`ml/features/stylometry.py`) using pure-CPU statistical indicators (TTR, Hapax, POS distribution entropy, sentence length variance, and negation density).
