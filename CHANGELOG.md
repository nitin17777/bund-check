# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-11-21
- Repository initialization and directory scaffolding (`frontend/`, `backend/`, `ml/`, `tests/`, `datasets/`, `docs/`).
- `AGENTS.md`: Mandatory operational rules for AI assistants and contributors (context acquisition, no faked APIs/mocks, testing enforcement, hardware boundaries).
- `GEMINI.md`: Antigravity/Gemini execution guidance.
- `PROJECT_STATUS.md`: Initial project tracking matrix with phase roadmap and test log templates.
- `docs/ARCHITECTURE.md`: Complete system architecture specification, Mermaid component and data flow diagrams, provider abstraction, persistence policies, and security/privacy safeguards.
- `docs/AI_MODEL_DESIGN.md`: Deep detection methodology, multi-signal ensemble, calibration, abstain bands, evaluation metrics, writing improver design with protected span extraction, and post-rewrite verification engine.
- `docs/API_SPEC.md`: Exhaustive REST API specification with Pydantic v2 schemas and error envelopes for `/api/v1/...` endpoints.
- `docs/DEVELOPMENT_ROADMAP.md`: Phases 0 through 10 with technical milestones, dependency graph, and PostgreSQL DDL schema with retention/deletion rules.
- `.gitignore` for Python, Node.js, Next.js, PyTorch models, and datasets.
