# Development Roadmap & Database Schema

## 1. Phased Execution Roadmap

The roadmap establishes 11 discrete phases (0 through 10) organized strictly by dependency ordering. No phase may proceed until its preceding dependency phase has passed all functional and unit verification tests.

```
Phase 0: Scaffolding, Architecture, Specs & Environment Setup
   │
   ▼
Phase 1: Document Extraction & Text Normalization Pipeline
   │
   ▼
Phase 2: Statistical & Stylometric Feature Extraction Engine
   │
   ▼
Phase 3: Transformer Classifier, Perplexity Signal & Model Ensemble
   │
   ▼
Phase 4: Probability Calibration, Uncertainty & Sentence Attribution
   │
   ▼
Phase 5: Writing Improver Engine & Protected Span Extraction
   │
   ▼
Phase 6: Post-Rewrite Verification Layer & Semantic Audit
   │
   ▼
Phase 7: FastAPI Core Services, Async Jobs & REST API Endpoints
   │
   ▼
Phase 8: Next.js Frontend — Analysis Dashboard & Interactive Diff View
   │
   ▼
Phase 9: End-to-End Integration, Security Hardening & Rate Limiting
   │
   ▼
Phase 10: Docker Deployment, Benchmarking & Documentation Finalization
```

---

### Phase Breakdown

#### Phase 0: Scaffolding, Architecture, Specs & Environment Setup (ACTIVE)
- **Goal**: Establish project directory topology, mandatory contributor protocols (`AGENTS.md`, `GEMINI.md`), architectural documentation, API specifications, and initial git repository.
- **Dependencies**: None.
- **Deliverables**: All foundational Markdown specifications, `.gitignore`, initial git commit. No application code.

#### Phase 1: Document Extraction & Text Normalization Pipeline
- **Goal**: Implement robust, secure text ingestion for PDF, DOCX, and TXT files.
- **Dependencies**: Phase 0.
- **Components**: `backend/services/parser/`, PyMuPDF (`fitz`), `python-docx`, character encoding detector (`charset-normalizer`), sentence boundary tokenizer (`nltk`/`spaCy`).
- **Verification Gates**: Passes magic byte checks, 10MB limits, decompression bomb tests, macro rejections, and extracts clean paragraph/sentence hierarchies.

#### Phase 2: Statistical & Stylometric Feature Extraction Engine
- **Goal**: Build pure-CPU, fast statistical signal extractors.
- **Dependencies**: Phase 1.
- **Components**: `ml/features/stylometry.py`, lexical richness (TTR, Hapax Legomena), POS tag distributional entropy, punctuation/readability metrics.
- **Verification Gates**: Unit tests verify deterministic outputs on standardized reference texts with runtime under 50ms for 1,000 words.

#### Phase 3: Transformer Classifier, Perplexity Signal & Model Ensemble
- **Goal**: Implement small local LM perplexity evaluator and transformer classifier head; combine with stylometric signals into an ensemble model.
- **Dependencies**: Phase 2.
- **Components**: `ml/models/perplexity.py` (quantized `distilgpt2` or `pythia-160m`), `ml/models/classifier.py` (`distilroberta`), `ml/models/ensemble.py` (Gradient Boosting / Logistic Regression).
- **Verification Gates**: Combined memory footprint stays under 2.0 GB VRAM / 4 GB system RAM. Offload training scripts for Kaggle/Colab documented in `ml/train/`.

#### Phase 4: Probability Calibration, Uncertainty & Sentence Attribution
- **Goal**: Implement Isotonic Regression calibration, the abstain band ($0.40 - 0.60$), and sentence-level attribution.
- **Dependencies**: Phase 3.
- **Components**: `ml/calibration/isotonic.py`, `ml/explainability/attribution.py`.
- **Verification Gates**: ECE (Expected Calibration Error) drops significantly post-calibration; synthetic prediction probabilities inside the abstain band trigger inconclusive statuses; sentence highlights correlate with high-perplexity deviations.

#### Phase 5: Writing Improver Engine & Protected Span Extraction
- **Goal**: Implement deterministic span protection and the swappable LLM provider adapter for 6 writing modes.
- **Dependencies**: Phase 0, Phase 1.
- **Components**: `backend/services/improver/masker.py`, `backend/services/improver/providers/` (`GroqProvider`, `OpenRouterProvider`, `AnthropicProvider`, `OpenAIProvider`, `LocalStubProvider`).
- **Verification Gates**: Placeholder tokens (`{{NUM_1}}`, `{{CITE_1}}`) are completely preserved across transforms and successfully restored without corruption.

#### Phase 6: Post-Rewrite Verification Layer & Semantic Audit
- **Goal**: Build automated verification audit for numbers, citations, named entities, paragraph counts, embedding similarity, and NLI contradiction checks.
- **Dependencies**: Phase 5.
- **Components**: `backend/services/improver/verifier.py`, `sentence-transformers` (`all-MiniLM-L6-v2`), local NLI checker (`cross-encoder/nli-deberta-v3-small`).
- **Verification Gates**: Unit tests catch injected missing numbers, dropped citations, and semantic contradictions; emits structured `VerificationReport` with appropriate severity ratings.

#### Phase 7: FastAPI Core Services, Async Jobs & REST API Endpoints
- **Goal**: Implement and test all REST endpoints defined in `docs/API_SPEC.md`.
- **Dependencies**: Phases 1, 4, 6.
- **Components**: `backend/routers/`, `backend/core/config.py`, Pydantic v2 schemas, database models via SQLAlchemy / Alembic.
- **Verification Gates**: 100% of endpoints conform to `API_SPEC.md`; error payloads strictly match RFC 7807 problem details; test suite passes with `pytest`.

#### Phase 8: Next.js Frontend — Analysis Dashboard & Interactive Diff View
- **Goal**: Build modern, accessible Next.js TypeScript interface with rich diff staging and calibration visualizations.
- **Dependencies**: Phase 7.
- **Components**: `frontend/app/`, Tailwind CSS, Lucide icons, document upload dropzone, side-by-side token diff view with accept/reject buttons per edit.
- **Verification Gates**: End-to-end user flows functional in browser; zero hydration errors; responsive layout across mobile and desktop.

#### Phase 9: End-to-End Integration, Security Hardening & Rate Limiting
- **Goal**: Integrate rate limiting, security headers, upload hardening, content-free logging, and comprehensive integration testing.
- **Dependencies**: Phase 8.
- **Components**: Token-bucket middleware, magic-byte validator middleware, `structlog` sanitizer, Vitest & Playwright test suites.
- **Verification Gates**: Ingestion attacks (decompression bombs, malformed PDFs) safely rejected; rate limiter halts burst traffic; zero document text leaked to server logs.

#### Phase 10: Docker Deployment, Benchmarking & Documentation Finalization
- **Goal**: Containerize application via Docker Compose; benchmark latency and memory footprint on RTX 2050 target profile.
- **Dependencies**: Phase 9.
- **Components**: `docker-compose.yml`, multi-stage `Dockerfile` (frontend, backend/ML), load testing scripts, finalized developer documentation.
- **Verification Gates**: `docker compose up` spins up healthy services; total VRAM usage stays strictly under 4.0 GB; system functions fully within 24 GB RAM.

---

## 2. PostgreSQL Relational Database Schema

All database interactions utilize PostgreSQL 16. Persistent document storage is **opt-in only** (`store_history == true`). By default, text is handled entirely in memory.

### Justification on `pgvector` & `Redis`:
- **`pgvector`**: Not required in initial phases. The semantic verification layer compares only *source paragraph $i$* with *target paragraph $i$* in-memory using small cosine dot-products. Vector indexing over large corpuses is unnecessary.
- **`Redis`**: In-memory token bucket rate limiting and background task queues (via Python `asyncio` or Celery) are sufficient for Phase 0-7. Redis will only be introduced if horizontal multi-instance synchronization is required in Phase 9.

---

### DDL Schema Proposal

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Settings & Encrypted Provider Keys
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    store_history_default BOOLEAN NOT NULL DEFAULT FALSE,
    default_improver_mode VARCHAR(50) NOT NULL DEFAULT 'academic_clarity',
    sensitivity_preference VARCHAR(30) NOT NULL DEFAULT 'balanced',
    encrypted_groq_key BYTEA NULL,
    encrypted_openrouter_key BYTEA NULL,
    encrypted_anthropic_key BYTEA NULL,
    encrypted_openai_key BYTEA NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Opt-in Documents Table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    word_count INTEGER NOT NULL,
    char_count INTEGER NOT NULL,
    encrypted_raw_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    retention_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

-- Index for scheduled deletion cleanup jobs
CREATE INDEX idx_documents_retention ON documents(retention_expires_at);
CREATE INDEX idx_documents_user_id ON documents(user_id);

-- 4. Opt-in Analyses Table (Module A: Checker)
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    calibrated_score NUMERIC(5, 4) NOT NULL,
    classification_band VARCHAR(50) NOT NULL,
    uncertainty_lower NUMERIC(5, 4) NOT NULL,
    uncertainty_upper NUMERIC(5, 4) NOT NULL,
    signals JSONB NOT NULL,
    sentence_attribution JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    retention_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_retention ON analyses(retention_expires_at);

-- 5. Opt-in Revisions Table (Module B: Improver)
CREATE TABLE revisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    mode VARCHAR(50) NOT NULL,
    original_text TEXT NOT NULL,
    rewritten_text TEXT NOT NULL,
    diff_data JSONB NOT NULL,
    verification_status VARCHAR(50) NOT NULL,
    verification_report JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    retention_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

CREATE INDEX idx_revisions_user_id ON revisions(user_id);
CREATE INDEX idx_revisions_retention ON revisions(retention_expires_at);
```

---

## 3. Retention & Deletion Lifecycle Controls

1. **Automatic Ephemeral Expiration**:
   - Opted-in documents, analyses, and revisions possess a mandatory `retention_expires_at` timestamp defaulting to 30 days.
   - An asynchronous cleanup worker executes daily:
     ```sql
     DELETE FROM documents WHERE retention_expires_at <= CURRENT_TIMESTAMP;
     DELETE FROM analyses WHERE retention_expires_at <= CURRENT_TIMESTAMP;
     DELETE FROM revisions WHERE retention_expires_at <= CURRENT_TIMESTAMP;
     ```
2. **Immediate User-Triggered Hard Deletion**:
   - Calling `DELETE /api/v1/delete` with `{"target": "all_user_data"}` executes a cascade delete across `users`, removing all settings, encrypted credentials, documents, analyses, and revisions instantly.
   - Calling `DELETE /api/v1/delete` with `{"target": "document", "id": "..."}` purges the specific document and its associated records immediately.
