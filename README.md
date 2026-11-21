# BundCheck (AI Content Checker + Writing Improver)

Production-minded, statistically calibrated AI-text analysis platform and writing refinement assistant.

> **CRITICAL ARCHITECTURAL NOTICE**:
> 1. **No Absolute Authorship Claims**: The detector module provides probabilistic analysis with explicit uncertainty, calibrated confidence bands, and human-in-the-loop review flags. It will never claim absolute proof of human or synthetic origin.
> 2. **Legitimate Writing Refinement**: The improver module is designed and tuned exclusively for stylistic enhancement, accessibility, and clarity. It strictly preserves facts, numbers, citations, and terminology, and is not marketed or engineered for detector evasion.

---

## Workspace Structure

```
bund-check/
├── AGENTS.md                  # Operational protocol for AI agents & contributors
├── GEMINI.md                  # Directives for Gemini/Antigravity execution
├── PROJECT_STATUS.md          # State of the project, phases, and verified tests
├── CHANGELOG.md               # Chronological log of changes
├── README.md                  # Repository overview
├── docs/                      # Architectural, ML, and API specifications
│   ├── ARCHITECTURE.md        # System architecture, data flow, security & privacy
│   ├── AI_MODEL_DESIGN.md     # ML pipeline, features, evaluation, improver & verification
│   ├── API_SPEC.md            # REST API schemas and endpoint contracts
│   └── DEVELOPMENT_ROADMAP.md # Phase execution plan (0-10) and DB schema
├── frontend/                  # Next.js + TypeScript + Tailwind CSS application
├── backend/                   # FastAPI + Pydantic v2 application
├── ml/                        # ML feature extraction, training pipelines, model artifacts
├── datasets/                  # Benchmark and calibration data (gitignored except .gitkeep)
└── tests/                     # Unit, integration, and end-to-end test suites
```

---

## Technical Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Lucide icons, Vitest / Playwright.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, PyMuPDF, python-docx, structlog.
- **Machine Learning**: PyTorch, Transformers, HuggingFace, scikit-learn, sentence-transformers, spaCy / NLTK.
- **Database & State**: PostgreSQL 16 (JSONB for signals, relational for users and revisions).
  - *Note*: `pgvector` and `Redis` are deferred until Phase 6 with explicit justification.
- **Infrastructure**: Docker, Docker Compose, environment-variable configuration (`.env.example`).
- **Target Local Hardware**: Intel/AMD x86_64 CPU, 24 GB System RAM, NVIDIA RTX 2050 (4 GB VRAM).
  - Large transformer model fine-tuning and heavy inference run on remote resources (Kaggle/Colab or hosted API providers via unified adapter abstractions).

---

## Core Modules

### 1. Module A: Probabilistic Content Checker
- Multi-signal extraction: Small local LM perplexity/entropy/burstiness, statistical stylometry, fine-tuned transformer classifier heads, and logistic regression / gradient boosting ensemble.
- Isotonic regression / Platt calibration.
- Explicit **abstain band** (e.g., $0.40 - 0.60$) indicating inconclusive statistical variance.
- Token and sentence-level contribution attribution.
- Zero "Ask an LLM if this is AI" prompts.

### 2. Module B: Writing Improver & Verification Layer
- Style rewriting across 6 distinct modes (*Natural/Conversational*, *Academic Clarity*, *Professional*, *Simple/Readable*, *Concise*, *Formal*).
- Deterministic **Protected Span Extraction** (regex + NER) protecting numbers, citations, URLs, equations, and code blocks with typed tokens.
- **Verification Layer**: Multi-layer post-generation audit:
  - Numeric value consistency diff.
  - Citation and reference diff.
  - Named entity preservation check.
  - Paragraph count alignment.
  - Semantic similarity via cross-sentence embeddings.
  - Contradiction detection via Natural Language Inference (NLI).
- Interactive change acceptance/rejection diff interface.

---

## Getting Started

Refer to [DEVELOPMENT_ROADMAP.md](file:///d:/bund-check/docs/DEVELOPMENT_ROADMAP.md) for the active development phase and [AGENTS.md](file:///d:/bund-check/AGENTS.md) for operational engineering constraints.
