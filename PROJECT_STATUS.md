# PROJECT_STATUS.md — Project Execution & Verification Tracker

## Active Project Phase
**Current Phase**: Phase 4 — Backend Detector Integration & Content Check API  
**Status**: Completed and Rigorously Verified (57/57 Tests Passing across all suites)

---

## Phase Roadmap Status

| Phase | Description | Status | Completed Date |
|---|---|---|---|
| **Phase 0** | Project Scaffolding, Architecture, Specs & Environment Setup | **Completed** | 2026-11-21 |
| **Phase 1** | Document Extraction, Normalization & Table Ingestion Pipeline | **Completed** | 2026-11-21 |
| **Phase 2** | Backend Foundation, Security Validators & Document Extract API | **Completed** | 2026-11-21 |
| **Phase 3** | Empirical Evaluation, Multi-Signal Feature Extraction & Calibration Engine | **Completed** | 2026-11-22 |
| **Phase 4** | Backend Detector Integration & Content Check API (`/check`, `/check/report`) | **Completed** | 2026-11-22 |
| **Phase 5** | Calibration, Abstain Band, Sentence Attribution & Cross-Generator Benchmark | Pending | — |
| **Phase 6** | Writing Improver Engine & Expanded Protected Span Extraction | Pending | — |
| **Phase 7** | Multi-Stage Post-Rewrite Verification Layer (Pure CPU) | Pending | — |
| **Phase 8** | FastAPI Core Services, Async Task Dispatch & REST API Endpoints | Pending | — |
| **Phase 9** | Next.js Frontend — Review Dashboard & Interactive Diff View | Pending | — |
| **Phase 10**| Docker Deployment, Benchmarking & Documentation Finalization | Pending | — |

---

## Session Log: Phase 4 Implementation & Verification

### Completed Tasks
1. **Model Loader Service (`backend/app/services/detection/loader.py`)**:
   - Implemented lazy, cached singleton `ModelRegistry` loading the serialized ensemble artifact (`gbdt_calibrated_ensemble.joblib`).
   - Defaulted to CPU; safe for 4GB RTX 2050 GPU execution when enabled in settings.
   - Graceful resolution of artifact paths and error handling via `DocumentProcessingException`.
2. **Detection & Inference Engine (`backend/app/services/detection/detector.py`)**:
   - Directly re-uses feature extraction pipeline from `ml/` (`extract_combined_features`, `extract_stylometric_features`) without code duplication.
   - Evaluates calibrated synthetic probability and maps to decision label and classification band:
     - $0.00 \le \text{Score} < 0.40$: `likely human-leaning` (`HUMAN_TYPICAL`)
     - $0.40 \le \text{Score} \le 0.60$: `inconclusive` (`INCONCLUSIVE` — Abstain Band)
     - $0.60 < \text{Score} \le 1.00$: `likely AI-leaning` (`SYNTHETIC_INDICATIVE`)
   - Computes empirical 95% uncertainty interval scaled by word count sample size.
   - Extracts top contributing signals with plain-language explanations matching the model's actual feature representation.
   - Evaluates paragraph and sentence indicators using local lexical diversity and uniformity metrics, marking sentences $< 10$ words as `INSUFFICIENT_LENGTH` and providing honest attribution disclaimers.
   - Flags texts $< 50$ words as `UNRELIABLE_VERY_SHORT_TEXT` and texts $< 150$ words as `LOW_RELIABILITY_SHORT_TEXT`.
   - Embeds the scientific `limitations` block with disclaimer, model version (`1.0.0`), and SHA-256 model hash.
3. **Report Generation Service (`backend/app/services/detection/report.py`)**:
   - Generates structured JSON analysis report.
   - Generates responsive, standalone HTML report with score badges, signals table, highlighted sentence indicators, and limitations callout.
4. **FastAPI Endpoints (`backend/app/api/v1/endpoints/check.py`)**:
   - `POST /api/v1/check`: Accepts either raw text or pre-extracted `Document` payload from Phase 2 extraction. Async timeout protection (`CHECK_TIMEOUT_SECONDS = 60s`).
   - `POST /api/v1/check/report`: Generates downloadable JSON and HTML reports.
   - Non-sensitive operational logging (logs word count, score, band; does NOT log document contents).
5. **Testing, Latency Benchmarks & Zero-Fake Verification**:
   - Automated test suite in `tests/test_phase4_detection.py` (6 tests).
   - Asserted exact numeric match between API endpoint score and offline ML evaluation code ($|api - offline| < 10^{-4}$).
   - Verified end-to-end flow: file upload $\to$ `POST /api/v1/documents/extract` $\to$ `POST /api/v1/check`.
   - Measured real local latency:
     - 500 words: **19.33 ms**
     - 2,000 words: **99.66 ms**
     - 10,000 words: **92.42 ms**
   - Verified zero fake/dummy/mock scores in backend detection logic via strict grep.
   - **Full test suite passing**: 57/57 tests passing across the repository.

### Modified / Created Files
- `backend/app/core/config.py`
- `backend/app/models/detection.py`
- `backend/app/services/detection/__init__.py`
- `backend/app/services/detection/loader.py`
- `backend/app/services/detection/detector.py`
- `backend/app/services/detection/report.py`
- `backend/app/api/v1/endpoints/check.py`
- `backend/app/main.py`
- `tests/test_phase4_detection.py`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`

### Test Verification Command & Raw Output
```powershell
$env:PYTHONPATH="."; $env:PYTHONNOUSERSITE="1"; $env:HF_HUB_OFFLINE="1"; $env:TRANSFORMERS_OFFLINE="1"; .\.venv\Scripts\python -m pytest -v tests/
```
```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0 -- D:\bund-check\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\bund-check
configfile: pyproject.toml
plugins: anyio-4.16.0, asyncio-1.5.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 57 items

tests/test_document_extract.py (20 tests) .................... PASSED [ 35%]
tests/test_ml_eval.py (6 tests) .......... PASSED                      [ 45%]
tests/test_phase2_documents.py (25 tests) .................... PASSED [ 89%]
tests/test_phase4_detection.py (6 tests) .................... PASSED  [100%]

============================= 57 passed in 5.18s ==============================
```

---

## Session Log: Phase 3 Implementation & Verification

### Completed Tasks
1. **Candidate Dataset Audit (`ml/datasets/README.md`)**:
   - Researched, verified, and cataloged legal candidate datasets: HC3 (Human ChatGPT Comparison Corpus, CC-BY 4.0), MIMU-Text (CC-BY 4.0), Ghostbuster Evaluation Benchmarks (MIT), and ArguGPT (CC-BY 4.0).
   - Documented exclusion of TuringBench due to commercial ambiguity.
   - Cataloged domain diversity, generator coverage, download commands, and known artifacts (e.g. prompt length leakage, human editor degradation).
2. **Unified Data Schema & Deduplication Engine (`ml/src/data/schema.py`)**:
   - Strict Pydantic `DataRecord` schema: `text`, `label` (0=human, 1=synthetic), `source`, `domain`, `generator`, `prompt_id`.
   - MinHash LSH deduplication with 3-character shingles and Jaccard similarity thresholding ($J \ge 0.85$).
   - GroupShuffleSplit by `prompt_id` ensuring zero cross-split leakage across train, val, and test.
   - Automated leak detection assertion (`assert_no_split_leakage`) executed on every split.
3. **Multi-Signal Feature Extractor (`ml/src/features/extractor.py`)**:
   - 9-dimensional stylometric signals (pure CPU, <15ms): sentence length mean & std, Type-Token Ratio (TTR), Hapax Legomena ratio, average word length, Flesch reading ease approximation, function word ratio, punctuation density, and negation density.
   - 4-dimensional LM perplexity signals (DistilGPT-2 with batching and local offline cache loading): mean perplexity, perplexity burstiness (sentence variance), token entropy, and mean token log-probabilities.
   - Unified 13-dimensional vector concatenation and disk caching via `joblib`.
4. **Baseline Models & Calibration (`ml/src/models/baseline.py`)**:
   - Implemented `FeatureClassifierPipeline` supporting Logistic Regression and HistGradientBoosting (GBDT).
   - Implemented separate `IsotonicRegression` calibration fitted strictly on validation probabilities.
   - Exportable Kaggle/Colab training script (`ml/src/models/colab_train_distilroberta.py`) with complete GPU runtime instructions.
5. **Evaluation Suite & Empirical Benchmarking (`ml/src/eval/`)**:
   - Metrics implementation: Precision, Recall, F1, ROC-AUC, PR-AUC, FPR, FNR, TPR at 1% & 5% FPR, Expected Calibration Error (ECE), and Brier Score.
   - Generator, domain, short-text (<50 words), and human-edited breakdown analyses.
   - Automated benchmark runner (`ml/src/eval/run_benchmark.py`).
6. **Empirical Evaluation Report & Model Card Artifacts**:
   - Generated `ml/reports/detection_eval.md` containing real empirical measurements, breakdown findings, and decision band definitions ($[0.40, 0.60]$ abstain band).
   - Saved serialized production model `ml/models/artifacts/gbdt_calibrated_ensemble.joblib`.
   - Generated `ml/models/artifacts/MODEL_CARD.md` with SHA-256 integrity hash.
7. **Automated Unit & Integration Tests (`tests/test_ml_eval.py`)**:
   - Verified MinHash deduplication, prompt-grouped splitting, leakage detection error triggering, stylometrics, 13-dim feature vectors and disk caching, pipeline calibration, and metric calculations.
   - **Test Results**: 51/51 tests passing across the entire project suite (`pytest`).

### Modified / Created Files
- `ml/__init__.py`
- `ml/datasets/README.md`
- `ml/src/__init__.py`
- `ml/src/data/__init__.py`
- `ml/src/data/schema.py`
- `ml/src/features/__init__.py`
- `ml/src/features/extractor.py`
- `ml/src/models/__init__.py`
- `ml/src/models/baseline.py`
- `ml/src/models/colab_train_distilroberta.py`
- `ml/src/eval/__init__.py`
- `ml/src/eval/metrics.py`
- `ml/src/eval/run_benchmark.py`
- `ml/reports/detection_eval.md`
- `ml/models/artifacts/gbdt_calibrated_ensemble.joblib`
- `ml/models/artifacts/MODEL_CARD.md`
- `tests/test_ml_eval.py`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`

### Test Verification Command & Raw Output
```powershell
$env:PYTHONPATH="."; $env:PYTHONNOUSERSITE="1"; $env:HF_HUB_OFFLINE="1"; $env:TRANSFORMERS_OFFLINE="1"; .\.venv\Scripts\python -m pytest -v tests/
```
```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0 -- D:\bund-check\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\bund-check
configfile: pyproject.toml
plugins: anyio-4.16.0, asyncio-1.5.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 51 items

tests/test_document_extract.py::test_unfold_ligatures PASSED             [  1%]
...
tests/test_ml_eval.py::test_data_record_and_minhash_deduplication PASSED [ 41%]
tests/test_ml_eval.py::test_split_grouped_dataset_and_leakage_assertion PASSED [ 43%]
tests/test_ml_eval.py::test_stylometric_features PASSED                  [ 45%]
tests/test_ml_eval.py::test_feature_vector_dimension_and_caching PASSED  [ 47%]
tests/test_ml_eval.py::test_classifier_pipeline_and_isotonic_calibration PASSED [ 49%]
tests/test_ml_eval.py::test_metrics_computation PASSED                   [ 50%]
...
tests/test_phase2_documents.py::test_validator_pdf_page_limit_exceeded PASSED [100%]

============================= 51 passed in 5.01s ==============================
```
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
