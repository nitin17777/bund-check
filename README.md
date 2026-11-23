# BundCheck

> **Statistically calibrated AI-text analysis and factual writing refinement platform.**

[![CI](https://github.com/your-org/bund-check/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Next.js: 14](https://img.shields.io/badge/Next.js-14-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)

---

## 1. What the Product Does

BundCheck provides two complementary engineering capabilities:

### Module A: Probabilistic Content Checker
- Evaluates documents for statistical signatures typical of machine-generated text (stylometric distributions, token-level burstiness, vocabulary richness, readability indices).
- Calibrated with Isotonic Regression to output an empirical **`synthetic_pattern_confidence`** score ($[0.0, 1.0]$) alongside an **uncertainty interval** (e.g., 95% confidence interval).
- Flags borderline inputs within an explicit **Abstain Band** ($0.40 - 0.60$) indicating inconclusive statistical evidence where editorial human review is required.
- Provides exploratory sentence-level heatmap indicators to inspect localized lexical uniformity.

### Module B: Factual Writing Improver & Verification Layer
- Refines prose across 6 stylistic modes (*Natural/Conversational*, *Academic Clarity*, *Professional*, *Simple/Readable*, *Concise*, *Formal*).
- Deterministic **Protected Span Extraction** automatically identifies and shields numbers, measurement units, dates, citations, equations, code, and named entities.
- Runs an automated multi-stage **Verification Audit** after generation:
  - Factual numerical consistency diff.
  - Citation and reference tracking (flags dropped or fabricated citations).
  - Negation and polarity preservation (detects inverted meaning).
  - Paragraph structural alignment.
  - Sentence-transformer semantic embedding similarity check.

---

## 2. Honest Scientific Limitations

### Limitations of Detection
1. **Never Claims Absolute Authorship**: Statistical patterns do not prove authorship. Human writing can exhibit high regularity, and model-generated text can be prompted to introduce synthetic variance.
2. **Domain Distribution Sensitivity**: Calibrated primarily on formal, academic, and journalistic prose. Performance degrades on creative fiction, dialogue, poetry, technical code documentation, and non-English texts.
3. **Short Sample Variance**: Documents under 150 words carry high estimation variance; inputs under 50 words are rejected from document-level classification.
4. **Adversarial Paraphrasing & Evasion**: Simple rewriting, synonym insertion, or intentional grammatical variations disrupt n-gram and stylometric heuristics.
5. **Not Probative Evidence**: Detection scores are exploratory indicators and must never be used as sole evidence for disciplinary, academic integrity, or legal actions.

### Limitations of Meaning Preservation
1. **Cosine Similarity is a Heuristic**: High embedding cosine similarity measures proximity in latent vector space; **it does not prove semantic equivalence or factual identity**.
2. **Pragmatic and Rhetorical Tone Shifts**: While factual spans (numbers, citations) are preserved, subtle rhetorical undertones, irony, or authorial voice may shift during stylistic rewriting.
3. **Complex Nested Tables & Layouts**: Complex multi-cell merged tables and custom graphical elements in DOCX/PDF uploads are cataloged as unsupported elements and skipped to prevent document corruption.

---

## 3. Architecture Overview

```
                      [ User Client / Browser ]
                                 │
                                 ▼
                     [ Caddy / Nginx TLS Proxy ]
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
      [ Next.js Frontend ]              [ FastAPI Backend ]
        Port: 3000                        Port: 8000
        • Document Dropzone               • Ingestion & Parser
        • Interactive Diff Editor         • Stylometric Engine
        • Sentence Heatmaps               • Ensemble Calibrator
        • Settings & Audit History        • Verification Audit
                                                  │
                                                  ▼
                                      [ PostgreSQL 16 DB ]
                                      • Opt-in Persistence
                                      • Session-based Auth
```

For complete technical specifications, see:
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): System architecture and data flow.
- [`docs/AI_MODEL_DESIGN.md`](docs/AI_MODEL_DESIGN.md): ML feature extractors, calibration, and verifier.
- [`docs/API_SPEC.md`](docs/API_SPEC.md): Typed REST API contracts.
- [`docs/BENCHMARK.md`](docs/BENCHMARK.md): Latency, throughput, and memory profiling.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Low-cost cloud deployment guide.

---

## 4. Quickstart & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18.18+ / 20+
- Git

### Option A: Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/bund-check.git
   cd bund-check
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY or OPENAI_API_KEY in .env if using the Improver
   ```

3. **Backend Setup**:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install --upgrade pip
   pip install -r backend/requirements.txt

   # Run database migrations (SQLite default for local dev)
   cd backend
   alembic upgrade head
   cd ..

   # Start backend API (port 8000)
   uvicorn backend.app.main:app --reload --port 8000
   ```

4. **Frontend Setup** (in a separate terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   # Access application at http://localhost:3000
   ```

---

### Option B: Production Docker Compose

Run the entire hardened production stack (Next.js, FastAPI, PostgreSQL 16, Caddy SSL Reverse Proxy):

```bash
cp .env.example .env
# Edit .env with your domain name and API keys

docker compose -f docker-compose.prod.yml up -d --build
```

---

## 5. Verification & Testing

Every commit and pull request runs automated tests across both layers:

### Running Backend Tests
```bash
python -m pytest tests/ -v --tb=short
```
*Current test suite: 164 automated tests covering extraction, ML feature evaluation, security hardening, rate limiting, and verification.*

### Running Frontend Tests
```bash
cd frontend
npm test
npm run lint
npm run build
```
*Current test suite: 51 Vitest unit tests covering UI diffing, heatmap rendering, and edge cases.*

---

## 6. Privacy & Data Retention Policy

- **Default Zero-Storage**: BundCheck operates under a strict ephemeral zero-storage default. Documents analyzed or revised are processed in memory and discarded immediately after response generation.
- **Opt-in Storage**: Users can explicitly opt into local analysis history via user settings. When opted in, records are subject to configurable automatic pruning (7, 30, or 90 days).
- **Zero Document Logging**: The structlog logging pipeline enforces automatic redaction filters ensuring that raw manuscript paragraphs, user identifiers, and provider API tokens are never written to disk or log streams.

---

## 7. Contributing

We welcome contributions to detection transparency, calibration methodology, and document parsing accuracy.

1. Fork the repository and create your feature branch: `git checkout -b feature/my-feature`.
2. Adhere to the code boundary rules defined in [`AGENTS.md`](AGENTS.md).
3. Ensure all tests pass: `pytest tests/` and `npm test`.
4. Submit a pull request with an atomic commit history following Conventional Commits format (`feat:`, `fix:`, `test:`, `docs:`).

---

## 8. License

Distributed under the MIT License. See `LICENSE` for more information.
