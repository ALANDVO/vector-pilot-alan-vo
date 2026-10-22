# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-10-22

### Added
- FastAPI backend with SQLite persistence
- React + TypeScript + Vite frontend
- Evaluation CRUD API with pagination and filtering
- Evaluation runs with model configuration
- Metrics tracking (accuracy, F1, custom metrics)
- OIDC authentication with Keycloak (realm export included)
- Role-based authorization (admin, operator, analyst)
- Dockerfiles for backend and frontend
- Docker Compose with Keycloak
- CI/CD workflow (backend tests, frontend build/test, Docker builds)
- 21 backend tests (API + service layer)
- 8 frontend tests (components + pages)
- Deterministic offline evaluation engine core
- LLM provider adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)