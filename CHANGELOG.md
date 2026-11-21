# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-11-22 (Phase 6: Multi-Stage Post-Rewrite Verification Layer)

#### New Services
- numbers.py - numeric/date/unit integrity checker; normalizes 1,000<->1000; CRITICAL on dropped/mutated values, WARN on introduced values
- citations.py - citation set diff (numbered [1], author-year, DOI); CRITICAL on dropped citations
- entities.py - spaCy NER entity diff with capitalized heuristic fallback (en_core_web_sm); CRITICAL on dropped entities
- structure.py - paragraph count alignment; WARN on PARAGRAPH_COUNT_MISMATCH (merge/split/delete/add)
- semantic.py - negation polarity keyword diff, cosine similarity via all-MiniLM-L6-v2, optional NLI via cross-encoder/nli-deberta-v3-small
- aggregate.py - runs all 5 checkers, determines PASSED/NEEDS_REVIEW/FAILED; per-paragraph breakdown at 1:1 alignment

#### New Endpoint
- POST /api/v1/verify - accepts {source_text, target_text, enable_nli}, returns VerificationReport with status, similarity score, severity-sorted findings, per-paragraph results, limitations in every response

#### Models Updated
- ImproveRequest: added run_verification (bool) and enable_nli (bool) flags
- ParagraphImprovement: added optional verification_report field
- run_improver_pipeline: wires per-paragraph verification when run_verification=True

#### Configuration Added
- SEMANTIC_SIMILARITY_THRESHOLD_PASS=0.88, SEMANTIC_SIMILARITY_THRESHOLD_REVIEW=0.75
- NLI_CONTRADICTION_THRESHOLD=0.10, ENABLE_NLI_BY_DEFAULT=False

#### Measured Precision/Recall (40-case fixture set)
- NEGATION_DROPPED: P=1.00 R=1.00
- PARAGRAPH_COUNT_MISMATCH: P=1.00 R=1.00
- CITATION_DROPPED: P=1.00 R=0.80
- NUMERIC_VALUE_DROPPED_OR_ALTERED: P=0.60 R=1.00
- ENTITY_DROPPED: P=0.44 R=0.80
- Full test suite: 111 passed, 1 skipped, 0 failures

---

### Added - 2026-11-22 (Phase 5: Writing Improver Pipeline & Protected Span Preservation)
- `backend/app/services/improver/providers/base.py`: Abstract `LLMProvider` interface defining standardized text generation with token and cost tracking.
- `backend/app/services/improver/providers/hosted.py`: Hosted provider implementation supporting Groq, OpenRouter, and OpenAI with secure key validation, error propagation, and pricing models.
- `backend/app/services/improver/providers/local.py`: Local small model provider for open-weight models (Qwen2.5-1.5B) with documented hardware constraints for 4GB VRAM and CPU fallback.
- `backend/app/services/improver/providers/factory.py`: Provider factory ensuring only genuine providers are instantiated in production.
- `backend/app/services/improver/protected_spans.py`: Protected span engine masking and unmasking citations, numbers, units, dates, DOIs, URLs, and code blocks, aborting with `PROTECTED_SPAN_DROPPED` if placeholders are dropped.
- `backend/app/services/improver/chunking.py`: Paragraph chunker preserving document ordering, heading structures, and brief preceding sentence contexts.
- `backend/app/services/improver/prompts.py`: Mode-specific prompt templates for all six approved modes (natural/conversational, academic clarity, professional, simple/readable, concise, formal) forbidding fact addition or terminology changes.
- `backend/app/services/improver/pipeline.py`: Improver coordination pipeline with backoff retries, sentence-level alignment for accept/reject review, and cost accounting.
- `backend/app/api/v1/endpoints/improve.py`: FastAPI endpoint `POST /api/v1/improve` with payload limits and privacy-preserving logging.
- `backend/app/models/improver.py`: Pydantic data models for improve requests, paragraph revisions, sentence changes, and usage accounting.
- `tests/test_phase5_improver.py`: 8 unit and integration tests verifying span masking, dropped span aborts, mode prompt divergence, heading preservation, pipeline execution via `FakeTestProvider`, missing key errors, and conditionally skipped live API tests.

### Added - 2026-11-22 (Phase 4: Backend Detector Integration & Content Check API)
- `backend/app/services/detection/loader.py`: Lazy, memory-safe singleton model registry loading the calibrated GBDT ensemble artifact (`gbdt_calibrated_ensemble.joblib`) on CPU by default with GPU-readiness for 4GB RTX 2050.
- `backend/app/services/detection/detector.py`: Core detection engine reusing feature extractors directly from `ml/`, applying Isotonic calibration, enforcing the 0.40–0.60 abstain band, computing empirical 95% uncertainty intervals, extracting top contributing signals with plain-language explanations, generating honest sentence-level indicators, and enforcing short-text length gating (<50 and <150 words).
- `backend/app/services/detection/report.py`: Comprehensive analysis report generator producing structured JSON and responsive, styled HTML reports including limitations, model version, and model hash.
- `backend/app/api/v1/endpoints/check.py`: FastAPI endpoints for `POST /api/v1/check` (supporting raw text or pre-extracted Document) and `POST /api/v1/check/report` with asyncio timeout protection and privacy-preserving logging (zero document text logged).
- `backend/app/models/detection.py`: Typed Pydantic models for check requests, check responses, contributing signals, sentence indicators, and limitations blocks.
- `tests/test_phase4_detection.py`: 6 automated unit and integration tests verifying schema conformance, exact numeric consistency between API and offline ML code, short-text length warnings, report exports, end-to-end extraction-to-check flow, and latency benchmarks (500, 2,000, and 10,000 words).

### Added - 2026-11-22 (Phase 3: Multi-Signal Evaluation, Feature Extraction & Detector Calibration)
- `ml/datasets/README.md`: Formal provenance audit of candidate datasets (HC3, MIMU-Text, Ghostbuster, ArguGPT) with license details, domain mappings, generator distributions, and documented exclusion of TuringBench.
- `ml/src/data/schema.py`: Unified `DataRecord` schema with label definitions (0=human, 1=synthetic), MinHash LSH deduplication across 3-character shingles, and `GroupShuffleSplit` by `prompt_id` with automated leakage detection assertions.
- `ml/src/features/extractor.py`: Multi-signal feature extractor computing 9 CPU stylometric metrics (sentence length stats, TTR, Hapax, Flesch reading ease, function word ratio, punctuation, negation density) and 4 LM metrics (mean perplexity, burstiness/sentence variance, token entropy, mean log-probs via DistilGPT-2 with batching and local caching) yielding a 13-dimensional feature representation with disk caching.
- `ml/src/models/baseline.py`: `FeatureClassifierPipeline` supporting Logistic Regression and HistGradientBoosting (GBDT) coupled with held-out validation `IsotonicRegression` probability calibration.
- `ml/src/models/colab_train_distilroberta.py`: Standalone, self-contained Google Colab / Kaggle script for fine-tuning `distilroberta-base` on GPU.
- `ml/src/eval/metrics.py`: Rigorous evaluation module computing Precision, Recall, F1, ROC-AUC, PR-AUC, FPR, FNR, Expected Calibration Error (ECE), Brier Score, and TPR at fixed 1% and 5% FPR operating points with generator and domain breakdowns.
- `ml/src/eval/run_benchmark.py`: End-to-end benchmark pipeline evaluating model baselines, writing the empirical evaluation report, saving model artifacts, and generating the Model Card.
- `ml/reports/detection_eval.md`: Empirical evaluation report detailing measured test metrics, breakdown vulnerabilities (short texts <50 words and human-edited machine text), model recommendation (calibrated GBDT ensemble), and calibrated decision bands (with a 0.40–0.60 abstain band).
- `ml/models/artifacts/gbdt_calibrated_ensemble.joblib`: Serialized calibrated GBDT ensemble artifact.
- `ml/models/artifacts/MODEL_CARD.md`: Production model card with SHA-256 integrity hash, training details, quantitative metrics, and plain-language limitations.
- `tests/test_ml_eval.py`: 6 automated unit and integration tests verifying schema validation, MinHash deduplication, leakage prevention, stylometrics, feature extraction shapes, calibration, and metric computation.

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
