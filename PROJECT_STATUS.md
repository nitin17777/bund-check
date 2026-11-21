# PROJECT_STATUS.md — Project Execution & Verification Tracker

## Active Project Phase
**Current Phase**: Phase 1 — Document Extraction, Normalization & Table Ingestion Pipeline  
**Status**: Completed and Rigorously Verified (20/20 Automated Tests Passing; Ready for Phase 2)

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

## Session Log: Phase 1 Final Verification & Edge Case Hardening

### Completed Tasks
1. **Full Project Test Suite Execution**:
   - Resolved Pytest-asyncio fixture scope warning by configuring `asyncio_default_fixture_loop_scope = "function"` and `asyncio_mode = "strict"` in `pyproject.toml`.
   - Resolved PyMuPDF deprecation warning by modernizing imports from `import fitz` to `import pymupdf as fitz`.
   - Test suite runs with **zero warnings and 100% passing results**.
2. **Security & Ingestion Edge Cases Added**:
   - Malformed DOCX with invalid ZIP headers / non-zip streams rejected with `SecurityValidationError`.
   - DOCX ZIP archive entry ceiling (> 1,000 entries) rejected as potential zip bomb.
   - Non-UTF8 byte streams in plain-text rejected with clean `SecurityValidationError`.
   - Complex merged-cell tables in DOCX automatically detected via cell proxy tracking, safely skipped, and logged in `unsupported_elements` metadata without failing paragraph extraction.
   - Async task failure handling: Verified that runtime exceptions in background tasks cleanly transition `TaskStatus` to `FAILED` and record the error message.
3. **Raw Text Immutability Verification**:
   - Added automated regression test `test_raw_text_immutability_verification` verifying that `ParagraphModel.raw_text` remains 100% byte-for-byte identical to the raw input, while `ParagraphModel.normalized_text` safely normalizes ligatures, line-break hyphens, and Unicode math.
4. **Roadmap & Phase Reconciliations**:
   - Reconciled phase milestones across `DEVELOPMENT_ROADMAP.md` and `PROJECT_STATUS.md`. Phase 0 and Phase 1 marked completed.

### Modified / Created Files
- `pyproject.toml` (Configured pytest-asyncio loop scope)
- `backend/services/parser/extractor.py` (Modernized PyMuPDF import; enhanced merged-cell table detection)
- `tests/test_document_extract.py` (Added 7 edge-case and security tests; modernized import)
- `docs/DEVELOPMENT_ROADMAP.md` (Reconciled phase statuses)
- `PROJECT_STATUS.md` (Updated test commands and results)
- `CHANGELOG.md` (Updated release log)

### Test Commands and ACTUAL Results
- **Command**:
  ```powershell
  $env:PYTHONPATH=""; $env:PYTHONNOUSERSITE="1"; .\.venv\Scripts\python -m pytest -v
  ```
- **Actual Raw Output**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0 -- D:\bund-check\.venv\Scripts\python.exe
  cachedir: .pytest_cache
  rootdir: D:\bund-check
  configfile: pyproject.toml
  testpaths: tests
  plugins: asyncio-1.5.0
  asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
  collecting ... collected 20 items

  tests/test_document_extract.py::test_unfold_ligatures PASSED             [  5%]
  tests/test_document_extract.py::test_stitch_hyphenated_linebreaks PASSED [ 10%]
  tests/test_document_extract.py::test_normalize_text_preserves_technical_content PASSED [ 15%]
  tests/test_document_extract.py::test_sentence_segmentation PASSED        [ 20%]
  tests/test_document_extract.py::test_file_size_validation PASSED         [ 25%]
  tests/test_document_extract.py::test_signature_and_null_byte_detection PASSED [ 30%]
  tests/test_document_extract.py::test_macro_document_rejection PASSED     [ 35%]
  tests/test_document_extract.py::test_decompression_bomb_rejection PASSED [ 40%]
  tests/test_document_extract.py::test_malformed_pdf_rejection PASSED      [ 45%]
  tests/test_document_extract.py::test_extract_txt_document PASSED         [ 50%]
  tests/test_document_extract.py::test_extract_docx_with_table PASSED      [ 55%]
  tests/test_document_extract.py::test_extract_pdf_document PASSED         [ 60%]
  tests/test_document_extract.py::test_async_task_manager_flow PASSED      [ 65%]
  tests/test_document_extract.py::test_docx_excessive_zip_entries_rejection PASSED [ 70%]
  tests/test_document_extract.py::test_docx_missing_required_openxml_structures PASSED [ 75%]
  tests/test_document_extract.py::test_docx_corrupted_zip_archive PASSED   [ 80%]
  tests/test_document_extract.py::test_invalid_utf8_txt_rejection PASSED   [ 85%]
  tests/test_document_extract.py::test_extract_docx_with_complex_merged_table PASSED [ 90%]
  tests/test_document_extract.py::test_async_task_manager_failure_handling PASSED [ 95%]
  tests/test_document_extract.py::test_raw_text_immutability_verification PASSED [100%]

  ============================= 20 passed in 1.34s ==============================
  ```

### Remaining Known Limitations
- The in-memory asyncio task manager is process-bound (server restart will drop unpersisted in-flight tasks). Persistent queuing (Redis/Celery) is planned for Phase 9.
- Complex nested/merged tables in PDF/DOCX are safely skipped and reported in `unsupported_elements` metadata rather than converted to markdown pipe-tables to preserve flow integrity.

### Outstanding Tasks for Next Phase
- **Phase 2 Initiation**: Implement pure-CPU Statistical & Stylometric Feature Extractor (`ml/features/stylometry.py`) for TTR, Hapax Legomena, POS entropy, sentence length variance, and negation density.
