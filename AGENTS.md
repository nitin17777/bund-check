# AGENTS.md — Mandatory Engineering Guidelines

> **CRITICAL**: Every AI agent, automated assistant, and human engineer operating in this repository must strictly adhere to the rules outlined in this document. Violations of these rules undermine production safety, model integrity, and project velocity.

---

## 1. Context Acquisition Protocol
1. **Always Read Status First**: Before executing any code, editing any file, or answering design questions, you must read:
   - `PROJECT_STATUS.md` to identify the active phase, recent changes, and outstanding tasks.
   - The relevant specification in `docs/` (`ARCHITECTURE.md`, `AI_MODEL_DESIGN.md`, `API_SPEC.md`, `DEVELOPMENT_ROADMAP.md`).
2. **Read Only Relevant Files**: Do not mass-read files across the repository. Targeted, batch reads of only the files pertinent to the current task minimize context exhaustion and avoid irrelevant edits.
3. **No Phantom Assumptions**: If an architectural detail or contract is undefined in `docs/`, check the roadmap or request clarification rather than inventing patterns out of band.

---

## 2. Code Modification & Quality Standards
1. **Make Targeted, Minimal Edits**: Edit only lines or blocks necessary to fulfill the immediate task. Avoid wholesale rewrites of files or reformatting lines you did not touch.
2. **Never Fake an API Response or Mock a Feature to Look Done**:
   - Do not return hardcoded dummy JSON from backend endpoints to pass them off as functional.
   - Do not write mock UI components that simulate completion without true backend or ML integration when a feature is marked complete.
   - If a subsystem is in development, use clear stubs that raise `NotImplementedError` or return structured HTTP 501 / error responses rather than fake success payloads.
3. **Never Mark a Feature Complete Without Running Tests**:
   - A phase or feature cannot be marked complete in `PROJECT_STATUS.md` unless its test suite has been executed and passed.
   - Every status update must record the exact test execution command and the actual raw output/result.
4. **Zero Hardcoded Secrets**:
   - API keys, database credentials, JWT secrets, and external provider tokens must be loaded via Pydantic Settings (`pydantic-settings`) reading from environment variables.
   - No secret, temporary test token, or production credential may ever be committed to git.

---

## 3. Architectural Boundary Separation
Strict boundaries between modules must be maintained:
- **`frontend/`**: Next.js React client and server components. Must never import backend or ML libraries. Must communicate with backend exclusively via typed HTTP REST requests defined in `docs/API_SPEC.md`.
- **`backend/`**: FastAPI REST API, routing, validation, database ORM/migrations, and document parsing. It interacts with `ml/` via clearly defined service interfaces and interfaces with external LLM providers via the unified provider abstraction.
- **`ml/`**: Model architectures, feature extractors, tokenizers, training scripts, calibration modules, and inference runners. Must remain decoupled from FastAPI request/response schemas.
- **`tests/`**: Unit, integration, and regression suites organized mirroring the project structure.

---

## 4. Hardware Constraints (RTX 2050 4GB VRAM / 24GB RAM)
- **Local Compute Limits**: The RTX 2050 (4 GB VRAM) cannot support 7B+ parameter model inference or fine-tuning locally.
- **Model Partitioning**:
  - Small models (e.g., lightweight BERT classifiers, DistilRoBERTa, DeBERTa-v3-small, or distilled sentence transformers) may run locally on CPU or 4GB VRAM with quantized/FP16 weights if strictly bounded.
  - Large language model inference (for the writing improver) must be routed through external/hosted providers (e.g., Groq, OpenRouter, Anthropic, OpenAI) via the swappable provider interface.
  - Fine-tuning of classifiers must be developed as exportable scripts targetable to Kaggle or Google Colab environments.

---

## 5. Session Closeout Protocol (Mandatory Checklist)
At the conclusion of every engineering or agent session, you must:
1. Update `PROJECT_STATUS.md`:
   - Summary of changes made in the session.
   - Exact files modified, created, or deleted.
   - Test execution commands run and the **ACTUAL results** (passed/failed counts).
   - Any newly discovered bugs or regressions.
   - Immediate next steps for the following session.
2. Update `CHANGELOG.md`:
   - Append a dated, structured log entry following Keep a Changelog format.
3. Git Commit Discipline:
   - Use atomic, logical git commits with conventional commit messages (e.g., `feat(api): ...`, `test(ml): ...`, `docs(arch): ...`).
   - Never combine unrelated changes across frontend, backend, and documentation in a single commit.
