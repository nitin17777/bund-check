# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-11-24 (Phase 10: Production Deployment, Packaging, Benchmarking & Acceptance)

#### Production Dockerization
- Created multi-stage non-root container definitions (`backend/Dockerfile` and `frontend/Dockerfile`) with automated healthcheck probes.
- Added `backend/entrypoint.sh` executing automatic Alembic database migrations (`alembic upgrade head`) on container startup.
- Added `backend/requirements.txt` with pinned versions for Python 3.11 production runtime.
- Added `docker-compose.prod.yml` orchestrating PostgreSQL 16, FastAPI, Next.js, and Caddy reverse proxy.
- Created `Caddyfile` for automated TLS certificate issuance, gzip/zstd compression, and HTTP/2 proxying.
- Authored `.env.example` documenting all configuration keys with local dev and production options.

#### Deployment Guide & Cost Profiling
- Published `docs/DEPLOYMENT.md` detailing low-cost cloud deployment architecture (< $20/month).
- Evaluated workload-to-hardware allocation (CPU vs. GPU vs. Hosted LLM).
- Profiled exact per-1,000-words improver costs across providers citing November 2026 pricing pages (Groq Llama 3.3 70B: ~$0.00201 / 1k words; OpenAI GPT-4o mini: ~$0.00104 / 1k words).

#### Documentation & Specification Alignment
- Updated `README.md` with complete architectural guide, honest limitations of detection and meaning preservation, setup instructions, testing commands, and privacy policies.
- Fixed specification drift in `docs/API_SPEC.md` aligning document extraction paths, health response contracts, and export formats with actual code.
- Verified fresh-clone reproduction in an isolated temporary directory.

### Added - 2026-11-24 (Phase 9: Hardening, Security, Benchmarking, CI/CD & Accessibility)

#### Test Suite Audit & CI
- Created `.github/workflows/ci.yml` defining full CI workflow (Python lint, pytest suite, frontend lint, Vitest, and production build).
- Added `tests/test_edge_cases.py` covering empty/whitespace text, oversized payloads, Pydantic improver mode validations, and async task manager lifecycle.
- Added `frontend/src/test/EdgeCases.test.tsx` verifying edge cases in diffing, large word shifts, and reject actions.
- Created `tests/conftest.py` with shared test application configuration.

#### Production Detector Evaluation
- Evaluated full production inference pipeline in `ml/reports/phase9_production_eval.md` on held-out test data.
- Added comprehensive 6-subsection limitations block detailing domain shifts, short-sample variances, and non-probative legal standing.

#### Security & Ingestion Hardening
- Implemented pure ASGI `SecurityHeadersMiddleware` in `backend/app/core/security.py` injecting HSTS, restrictive CSP, nosniff, DENY frame options, Permissions-Policy, and cache-control no-store headers.
- Performed upload fuzzing against decompression bombs, zip corruptions, null bytes, and spoofed extensions.
- Verified structlog sanitizers prevent sensitive manuscript content and API keys from leaking into log records.

#### Performance & Benchmarking
- Added `docs/BENCHMARK.md` documenting empirical latency and memory across 500 words (33 ms, 0.1 MB RAM), 5,000 words (695 ms, 0.8 MB RAM), and 20,000 words (10.9 s, 3.1 MB RAM).
- Validated feature caching and memory ceiling compliance (< 4 MB working RAM) adhering to RTX 2050 4GB VRAM limits.

#### Accessibility & UI Hygiene
- Audited all frontend routes and added missing `aria-label` attribute on the history search input.
- Verified dynamic data binding in `CheckerResults` confirming no fabricated numbers or hardcoded scores.

### Added - 2026-11-23 (Backend Phase 8: SQLAlchemy 2 + Alembic, Auth, Endpoints, Export)

#### SQLAlchemy 2 + Alembic Migrations
- Created SQLAlchemy 2.0 ORM models for users, user_settings, documents, analyses, and revisions
- All tables use opt-in persistence: only store data when user explicitly opts in
- Analyses can store scores and stats without document text when user has not opted in
- Alembic migration scripts support upgrade/downgrade with SQLite

#### Authentication
- Email + password login with argon2 password hashing
- Session management via httpOnly session cookies
- CSRF protection through cookie-based session validation
- No secrets in code - all credentials loaded from environment variables

#### API Endpoints
- `GET /api/v1/settings`: Retrieve user settings
- `PUT /api/v1/settings`: Update user settings (store_opt_in, default_improver_mode, sensitivity_preference, data_retention_days)
- `GET /api/v1/history`: List user's analysis and revision records
- `DELETE /api/v1/delete`: Hard delete of all user data or specific document with cascade
- `POST /api/v1/export`: Export final accepted text as DOCX, TXT, and PDF

#### Export Format Support
- **DOCX** (python-docx): Attempts to preserve headings, bold, italic, and simple lists; documents known losses
- **TXT**: Plain text round-trip export
- **PDF** (reportlab): Simple formatted PDF with title, headings, paragraphs, and basic styling

### Changed
- `backend/app/main.py`: Integrated new routers (users, settings, history, delete, export)
- `PROJECT_STATUS.md`: Updated with Phase 8 backend implementation summary

### Fixed
- Migration up/down now succeeds with SQLite
- No hardcoded secrets in code (all credentials from environment variables)

### Fixed - 2026-11-23 (Frontend Workspace Suite: Dashboard, History, Report Details, Settings & Local Opt-in Store)

#### Dashboard Workspace (`frontend/src/app/dashboard/page.tsx`)
- Integrated real-time backend health probe via `GET /api/v1/health` showing live status, version, and environment.
- Added live metric cards: engine status, calibrated abstain band (`[0.40 - 0.60]`), stored analyses count, and stored revisions count.
- Added quick action workflow shortcuts to Content Checker and Writing Improver.
- Implemented recent activity stream with direct report links when opted in, and proper zero-storage empty state for new users.

#### Audit History Workspace (`frontend/src/app/history/page.tsx`)
- Searchable and filterable history viewer supporting `All Records`, `Content Checks`, and `Writing Revisions`.
- Retention policy notice clarifying local-only storage posture.
- Individual record deletion with accessible confirmation modal (`Dialog`).
- Proper empty states for both unpopulated history and zero-match query results.

#### Report Detail Workspace (`frontend/src/app/reports/[id]/page.tsx`)
- Reuses `CheckerResults` and `SentenceHeatmap` to display full saved analysis audits, empirical uncertainty intervals, scientific limitations, model hash, and document statistics.
- Honest unpopulated empty state for non-persisted identifiers without fabricated scores or fake downloads.

#### System Settings Workspace (`frontend/src/app/settings/page.tsx`)
- "Store my documents" opt-in preference toggle (default OFF / strict zero-storage).
- Local retention window configuration (7, 30, 90 days).
- Default Writing Improver mode selector across all 6 editorial presets.
- Data portability: JSON export of all configured settings and saved audit records.
- Complete data purge with irreversible deletion confirmation dialog.
- Explicit "Phase 8 Roadmap" disclosure on cloud sync & remote account endpoints (`GET /api/v1/settings`, `DELETE /api/v1/delete`).

#### Local Opt-In Session Store (`frontend/src/lib/local-store.ts`)
- Client-side storage layer respecting privacy directives: persists records strictly when `storeOptIn` is true, with automated TTL pruning, export, and purge handlers.

#### Verification & Testing
- `frontend/src/test/DashboardAndSettings.test.tsx`: 11 Vitest unit and component tests covering local store operations, dashboard metrics, history search/filtering/deletion, settings persistence, and report detail rendering.
- All 46 frontend unit tests passing across 15 test suites; ESLint clean (0 warnings, 0 errors); production build passing (9/9 routes compiled and statically optimized).


### Added - 2026-11-22 (Writing Improver Workspace: Interactive Sentence Diffs, Verification Audit, and Undo/Redo Engine)

#### Writing Improver Workspace (`frontend/src/`)
- `frontend/src/app/humanizer/page.tsx`: Complete Writing Improver workspace page with dual-panel layout, dynamic mode selection across all 6 modes, real-time revision pipeline, jump-to-location smooth scrolling, and complete synchronization between sentence-level accept/reject decisions and the final manuscript.
- `frontend/src/lib/diff.ts`: Word-level diff algorithm using Longest Common Subsequence (LCS) tokenize engine guaranteeing exact preservation of original whitespace, punctuation, citations, and formulas.
- `frontend/src/components/improver/DiffView.tsx`: Dual-mode diff component supporting inline deletion/insertion (`<del>` / `<ins>`) and side-by-side comparison with syntax-highlighted diffs.
- `frontend/src/components/improver/SentenceChangeCard.tsx`: Sentence-aligned diff review card featuring individual Accept/Reject controls, status indicators (`Accepted`, `Rejected (Original Kept)`, `Unchanged`), inline verification advisory badges (`Critical Audit Flag`, `Review Advisory`), and an explicit confirmation dialog (`Dialog`) required before accepting revisions flagged with CRITICAL/WARN findings.
- `frontend/src/components/improver/VerificationPanel.tsx`: Audit breakdown grouped by category (Numbers, Citations, Entities, Structural Integrity, Semantic Drift) and severity (`CRITICAL`, `WARN`, `INFO`), jump-to-paragraph action buttons, heuristic disclaimer notice, and re-verification trigger.
- `frontend/src/components/improver/ImproverForm.tsx`: Input form with character/word counter, 6 editorial mode cards with descriptive summaries, provider selector override (`groq`, `openrouter`, `openai`, `local_small`), verification checkbox toggle, stage progress bar, and cancellation support.
- `frontend/src/components/improver/FinalTextEditor.tsx`: Editable final manuscript text editor serving as the source of truth for downstream export, complete with Accept All / Reject All actions, undo/redo history stack, copy-to-clipboard button, telemetry row displaying provider, model, tokens, and estimated cost, and a visibly disabled Download button with an explanatory tooltip (no fake download).

#### Verification & Testing
- `frontend/src/test/diff.test.ts`: 9 Vitest unit tests covering word tokenization, empty strings, insertions, deletions, substitutions, protected span tags, and text reconstruction.
- `frontend/src/test/ImproverWorkspace.test.tsx`: 6 Vitest component tests verifying inline/split diff rendering, accept/reject toggling, flagged critical change confirmation modal, undo/redo state manipulation, manual editing, and disabled download tooltip.
- `frontend/src/test/e2e-improver.spec.ts`: 16 Playwright E2E scenarios across Desktop Chrome and Mobile Chrome (Pixel 5) testing 6-mode rendering, word count updates, input validation, mode switching, verification toggling, mobile 375px layout usability, heuristic disclosure presence, and provider configuration against the live running server.
- All 35 Vitest unit tests passing (14 test files); 16/16 Playwright Writing Improver tests passing; 14/14 Playwright Content Checker tests passing; `next lint` zero warnings or errors; production build 100% successful.


### Added - 2026-11-22 (Phase 9: Security Hardening, Rate Limiting & Phase 7: Task Dispatch Engine)

#### Security Headers & Middleware
- `backend/app/core/security.py`: Implemented `SecurityHeadersMiddleware` adding `Strict-Transport-Security` (`max-age=63072000`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, restrictive `Content-Security-Policy` (`frame-ancestors 'none'`), and `Cache-Control: no-store, no-cache, must-revalidate, private` across all API responses.
- Implemented `X-Request-ID` tracing middleware assigning unique request identifiers and echoing them back for auditability.
- Restricted CORS configuration from wildcard to explicitly allowed origins in `backend/app/core/config.py`.

#### Rate Limiting Engine
- Integrated `slowapi` token-bucket rate limiter keyed by client remote IP.
- Enforced per-endpoint quotas: 20/min for document extraction, 30/min for content checking, 10/min for writing improvement, 30/min for standalone verification, 20/min for report downloads, and 120/min for task status polling.
- Implemented RFC 7807 429 error handler returning `TOO_MANY_REQUESTS` code and `Retry-After: 60` header.

#### Content-Free Structured Logging
- `backend/app/core/logging.py`: Configured `structlog` with dedicated `_sanitize_processor` intercepting and redacting sensitive document fields (`text`, `raw_text`, `original`, `revised`, `content`, `diff`, `prompt`, `completion`) and truncating long values $> 200$ chars to ensure zero document content is leaked into logs.
- Converted application startup/shutdown to modern FastAPI `lifespan` context manager eliminating deprecation warnings.

#### Task Dispatch & Polling Engine (Phase 7 Deliverable)
- `backend/app/core/task_manager.py`: Implemented thread-safe `InMemoryTaskManager` backed by `asyncio.create_task` and `asyncio.to_thread` with lifecycle states (`pending`, `processing`, `completed`, `failed`), progress fraction, and automatic 30-minute result TTL expiry.
- `backend/app/api/v1/endpoints/tasks.py`: Added `GET /api/v1/tasks/{task_id}` polling endpoint matching `API_SPEC.md § 3.4`.

#### Verification & Testing
- `tests/test_phase9_security.py`: Added 45 tests covering security headers, 429 rate limit triggers, ingestion attack defenses (empty files, null bytes, extension spoofing, macro detection, payload size ceiling, decompression bombs), task manager concurrency, structlog redaction, health schema, full file upload $\to$ check pipeline, and Unicode character offset alignment.
- Executed entire test suite: 156 passed, 1 skipped across all phases (100% pass rate).
- Verified Playwright E2E suite against live hardened backend (14/14 tests passing across Desktop Chrome and Mobile Chrome).

### Added - 2026-11-22 (Phase 8: Live AI Content Checker Workspace, Heatmap & Reports)

#### Checker Workspace & Heatmap (`frontend/src/`)
- `frontend/src/app/checker/page.tsx`: Workspace page integrating live document extraction, multi-signal check submission, dynamic stage progress, and analysis results view.
- `frontend/src/components/checker/CheckerForm.tsx`: Input form supporting paste text and drag-and-drop file upload (`.pdf`, `.docx`, `.txt`), real-time word counter with $<50$ word warning, multi-stage progress indicator (`extracting` $\to$ `analyzing`), cancel support via `AbortController`, and actionable error alerts for scanned PDFs (`SCANNED_PDF_OCR_NOT_SUPPORTED`), file size limits, short text, and empty submissions.
- `frontend/src/components/checker/CheckerResults.tsx`: Assessment banner displaying calibrated label (`likely human-leaning`, `inconclusive`, `likely AI-leaning`), empirical 95% uncertainty interval, prominent scientific limitations panel, document statistics, contributing signals cards, and report download triggers.
- `frontend/src/components/checker/SentenceHeatmap.tsx`: Heatmap highlighting sentences using exact API character offsets without drift on multi-paragraph Unicode manuscripts, sentence detail inspector drawer displaying local synthetic indicator and attribution disclaimer, and score range filter tabs (`All Sentences`, `Elevated Synthetic`, `Inconclusive`, `Human-Typical`).

#### Report Generation
- Integrated `/api/v1/check/report` to export standalone HTML and structured JSON reports containing full audit metadata, model version (`1.0.0`), and SHA-256 model hash.

#### Testing & Verification
- `frontend/playwright.config.ts` & `frontend/src/test/e2e-checker.spec.ts`: Full Playwright E2E suite covering 14 scenarios across Desktop Chrome and Mobile Chrome (Pixel 5) against the live backend (text paste, Unicode offset alignment, popover inspection, report downloads, file uploads for `.txt`, `.docx`, `.pdf`, scanned PDF 422 error, short text validation).
- `frontend/src/test/e2e-live-backend.mjs`: Standalone live backend verification script testing Unicode round-trip, extraction, check analysis, report export, and error codes.
- `frontend/src/test/CheckerResults.test.tsx` & `frontend/src/test/SentenceHeatmap.test.tsx`: Vitest component tests verifying calibrated label rendering, popover inspection, and tab filtering.
- Re-verified `next lint` (0 warnings, 0 errors) and `next build` (all 9 routes compiled and statically optimized).

### Added - 2026-11-22 (Phase 8: Frontend Design System, App Shell & Landing Page Foundation)

#### Design System & Tokens
- `frontend/tailwind.config.ts`: Custom deep obsidian surface tokens (`#090D16`, `#0E1422`, `#141C2E`, `#1A243B`), restrained accent color (`#3B82F6`), semantic palette (`info`, `success`, `warning`, `critical`), and strict border radius scale.
- `frontend/src/app/globals.css`: Dark mode variables, custom scrollbars, and `prefers-reduced-motion` compliance.
- `frontend/src/app/layout.tsx`: Real Google Font loading via `next/font/google` for Inter (UI) and JetBrains Mono (data/code).

#### UI Components (`frontend/src/components/ui/`)
- `Button.tsx`: Accessible button supporting variants (`primary`, `secondary`, `outline`, `ghost`, `destructive`), sizes (`sm`, `md`, `lg`), spinner loading state, and disabled semantics.
- `Card.tsx`: Flexible card system with `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, and `CardFooter`.
- `Tabs.tsx`: Accessible tab interface with keyboard navigation and ARIA state management.
- `Badge.tsx`: Status indicator pill supporting 7 semantic variants.
- `Tooltip.tsx`: Hover/focus tooltip with delay and directional positioning.
- `Dialog.tsx`: Modal dialog with focus trap, backdrop dismissal, and Escape key handling.
- `Toast.tsx`: Notification system with auto-dismiss, manual dismissal, and `useToast` hook.
- `Progress.tsx`: Accessible progress indicator supporting determinate and indeterminate modes.
- `Skeleton.tsx`: Motion-reduced pulse placeholder for asynchronous content loading.
- `FileDropzone.tsx`: Drag-and-drop and file-browse component with client-side file extension checking (`.pdf`, `.docx`, `.txt`) and 10 MB size ceiling validation.
- `EmptyState.tsx`: Accessible empty state component with icon, heading, description, and optional action buttons.

#### App Shell & Navigation (`frontend/src/components/layout/AppShell.tsx`)
- Fixed desktop sidebar (256px wide) with active route indicator, system status badge, and methodology link.
- Mobile responsive drawer with accessible hamburger toggle, backdrop blur, and focus management.
- Sticky top navigation bar with breadcrumb tracking and privacy mode indicators.

#### App Routes (`frontend/src/app/`)
- `/`: Methodology-first Landing Page with prominent scientific limitations disclosure and zero fabricated statistics.
- `/dashboard`: Operational overview and empty state for past activity.
- `/checker`: Content inspection view with document dropzone and text analysis input.
- `/humanizer`: Dual-pane writing improvement layout for source and revised text review.
- `/history`: Ephemeral audit history view explaining zero-retention defaults.
- `/reports/[id]`: Dynamic report lookup view with unpopulated record notification.
- `/settings`: System configuration overview for privacy retention, compute boundaries, and LLM endpoints.

#### Typed API Client (`frontend/src/lib/api-client.ts`)
- Strict typed client adhering to `docs/API_SPEC.md` contracts.
- Custom `ApiException` preserving RFC 7807 error envelopes (`code`, `message`, `details`, `request_id`).
- Universal `RequestState<T>` union type for predictable UI states.

#### Verification & Quality Gates
- 10 Vitest test suites, 17/17 passing unit tests.
- 0 ESLint warnings or errors (`next lint`).
- Next.js production build (`next build`) compiled 9 static and dynamic routes with zero errors.
- Axe-Core accessibility audit achieved 100% score across all 7 routes.
- Responsive audit verified seamless rendering across 375px, 768px, and 1280px viewports.
- Digits-in-copy review confirmed zero invented marketing statistics or fabricated user numbers.

---

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
