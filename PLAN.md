# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton-fastapi-react

## Roadmap

### skeleton-fastapi-react — Runnable FastAPI/React skeleton with core domain engine

Status: done

Acceptance:
- FastAPI backend with SQLite storage runs locally
- React + TypeScript + Vite frontend builds and runs
- One complete end-to-end workflow (create/read AI evaluation run)
- Backend tests pass (pytest)
- Frontend typecheck and tests pass
- Dockerfiles and compose.yaml for local development

Implementation: `backend/app/main.py`, `backend/app/api/v1/evaluations.py`, `backend/app/services/evaluation.py`, `backend/app/models/evaluation.py`, `backend/app/schemas/evaluation.py`, `frontend/src/App.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/components/EvaluationList.tsx`, `frontend/src/components/EvaluationForm.tsx`, `frontend/src/components/EvaluationDetail.tsx`

Tests: `backend/tests/test_api_evaluations.py`, `backend/tests/test_services_evaluation.py`, `frontend/src/components/EvaluationList.test.tsx`, `frontend/src/pages/Dashboard.test.tsx`

### oidc-keycloak-auth — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Keycloak realm import provided
- Backend validates JWT tokens with signature/issuer/audience
- Frontend implements PKCE flow with sessionStorage
- Role-based authorization on all data endpoints
- Tests cover unauthenticated rejection and role denial

### llm-adapters — LLM provider adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)

Status: planned

Acceptance:
- Configurable provider/model/endpoint via env vars
- httpx adapters with bounded timeouts and redacted errors
- Keys only server-side, opt-in advisory explanations

### ai-evaluation-engine — Substantive AI/ML evaluation engine with reproducible baselines

Status: planned

Acceptance:
- Domain engine beyond CRUD: agent reasoning evaluation, model quality, or RAG assessment
- Three complete workflows: create evaluation run, execute baseline, compare results
- Offline deterministic core works without LLM key
- Explicit metrics, small labeled dataset, limitations discussion

### packaging-docs — Packaging, documentation, and portfolio.json

Status: done

Acceptance:
- README with install/run/test steps, Mermaid diagram, API reference
- LICENSE MIT, CHANGELOG.md, portfolio.json at root
- pyproject.toml and package.json author metadata
- CI workflow tests backend/frontend, builds Docker images

Implementation: `README.md`, `LICENSE`, `CHANGELOG.md`, `portfolio.json`, `pyproject.toml`, `frontend/package.json`, `.github/workflows/ci.yml`, `compose.yaml`, `backend/Dockerfile`, `frontend/Dockerfile`, `keycloak/realm-export.json`, `.env.example`

