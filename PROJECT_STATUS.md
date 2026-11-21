# PROJECT_STATUS.md — Project Execution & Verification Tracker

## Active Project Phase
**Current Phase**: Phase 0 — Scaffolding, Architecture & Feasibility Audit  
**Status**: Feasibility Audit Approved & Specifications Revised (Ready for Phase 1 upon final user greenlight)

---

## Phase Roadmap Status

| Phase | Description | Status | Completed Date |
|---|---|---|---|
| **Phase 0** | Project Scaffolding, Architecture, Specs & Environment Setup | **In Progress** | — |
| **Phase 1** | Document Extraction, Normalization & Table Ingestion Pipeline | Pending | — |
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

## Session Log: Phase 0 Scaffolding & Feasibility Audit Revisions

### Completed Tasks
- Defined directory topology: `project/` root with `frontend/`, `backend/`, `ml/`, `tests/`, `datasets/`, `docs/`.
- Authored core governance docs: `AGENTS.md`, `GEMINI.md`, `README.md`, `CHANGELOG.md`.
- Completed independent senior engineering feasibility review (Prompt 0.5 audit).
- Integrated user-approved decisions and modifications across all system specifications:
  1. **Hardware & Model Partitioning**: Safe GPU usage for DistilGPT-2 & DistilRoBERTa with dynamic VRAM/RAM measurement (no fixed 1.4GB peak assumption), configurable mini-batching, and explicit CPU fallback. Verification models (MiniLM, NLI DeBERTa) pinned to CPU.
  2. **Detection Semantics**: Terminology standardized to `synthetic_pattern_confidence` with `HUMAN_TYPICAL`, `INCONCLUSIVE` (initial configurable $[0.40, 0.60]$ band), and `SYNTHETIC_INDICATIVE` bands. Minimum length (50 words) and low-reliability (150 words) established as initial design choices. Zero claims of absolute authorship proof.
  3. **Benchmarking Standards**: Explicit evaluation splits: (a) In-distribution generators, (b) Out-of-distribution unseen generators, (c) Human-edited AI text, and (d) Diverse human corpora. Performance tracked at strict $1\%$ and $5\%$ FPR operating points with prompt-disjoint leakage controls.
  4. **Meaning-Preservation Verification**: Expanded deterministic span protection for numbers, dates, units, negations, citations, and terms. Multi-tier verification flags dropped negations, date slips, and unit alterations. Embedding cosine similarity formally treated as a heuristic proximity check, not a semantic guarantee.
  5. **Asynchronous Architecture**: Implemented async task dispatch interface (`202 Accepted` + polling on `/tasks/{task_id}`) for text exceeding configurable 1,000-word threshold or file uploads, keeping background task abstraction upgradable without premature Redis/Celery bloat.
  6. **Document Parsing Clarification**: Cleanly distinguished standard grid tables (converted to Markdown pipe-tables) from unsupported nested structures (skipped and reported in `unsupported_elements` metadata). Added ligature unfolding and hyphen stitching.

### Modified / Created Files
- `docs/ARCHITECTURE.md` (Updated with async task data flow, table handling, and dynamic VRAM monitoring)
- `docs/AI_MODEL_DESIGN.md` (Updated with `synthetic_pattern_confidence`, configurable bands, benchmark classes, and expanded span protection)
- `docs/API_SPEC.md` (Updated with task polling endpoints, `synthetic_pattern_confidence`, table extraction schemas, and error definitions)
- `docs/DEVELOPMENT_ROADMAP.md` (Updated with revised phase gates, DDL schema, and retention controls)
- `PROJECT_STATUS.md` (Updated with session audit log)
- `CHANGELOG.md` (Updated with audit revisions)

### Test Commands and Actual Results
- Command: `git status`
  - *Result*: Tracked specification updates consistent across docs, API schemas, and roadmap.
- Command: Verification of zero application code or dependencies installed in Phase 0.
  - *Result*: Confirmed.

### Known Bugs / Technical Debt
- None (Planning and specifications phase).

### Outstanding Tasks Before Phase 1 Initiation
- Receive final user greenlight to proceed with Phase 1 implementation.
