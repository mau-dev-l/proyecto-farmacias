# Pharmacy inventory backend foundation
Branch: workspace (no Git repository detected)
Delivery strategy: single-pr
Test runner: pytest

## Specs
1. S1 — “Build the pharmacy inventory and expiration-control system incrementally: database, complete backend API, then frontend.”
   - Scope: establish the executable backend/database foundation first.
   - Acceptance: the backend has installable dependencies, environment configuration, a SQLAlchemy engine/session, and a FastAPI application.
2. S2 — “Use PostgreSQL with pgvector in Docker, database named `farmacias`; API connects to the container.”
   - Scope: local PostgreSQL/pgvector container and backend connection settings.
   - Acceptance: Compose exposes PostgreSQL on host port 5433 and initializes the existing schema.
3. S3 — “si procede, el main dejalo como main.py asi como esta”
   - Scope: preserve `backend/app/main.py` as the application entry point.
   - Acceptance: the documented startup command is `uvicorn app.main:app --reload` from `backend/`.

## Tasks
- T1 (S1-S3): inline — create Docker/database/backend foundation — status: completed — commit: n/a (no Git repository)
- T2 (S1): inline — add SQLAlchemy domain models and authentication foundation — status: completed — commit: n/a (no Git repository)
- T3 (S1): inline — add medicine catalog CRUD and search endpoints — status: completed — commit: n/a (no Git repository)
- T4 (S1-S2): inline — add lot inventory and transactional PEPS movements — status: completed — commit: n/a (no Git repository)
- T5 (S1-S3): inline — add alerts, reports, administration, and deferred integration stubs — status: completed — commit: n/a (no Git repository)
- T6 (S1-S3): inline — build the React/Vite frontend shell and core operational screens — status: completed — commit: n/a (no Git repository)

## Log
- L1: Build the pharmacy inventory and expiration-control system incrementally: database, complete backend API, then frontend. Start with the backend and leave LLM/RAG/LangChain/Telegram implementation pending.
- L2: Keep the main as `main.py` and use a valid Uvicorn import path.
- L3: Exploration found an empty backend scaffold, an existing SQL schema, and no Git repository.
- L4: T1 verification: Python compileall passed and `docker compose config --quiet` passed; pytest remains unavailable because pytest is not installed.
- L5: T2 verification: dependencies installed successfully and `python -m pytest tests -q` passed with 2 tests; Docker runtime verification is pending because the Docker daemon is unavailable.
- L6: T3 verification: `python -m pytest tests -q` passed with 2 tests and 2 third-party deprecation warnings.
- L7: T4 verification: pytest passed with 2 tests and compileall completed successfully; live PEPS/database verification remains pending until Docker is available.
- L8: T5 verification: pytest passed with 2 tests, compileall passed, and the application registered 30 routes including `/api/v1/bot/consulta`; Telegram/LLM routes intentionally return 501.
- L9: Frontend exploration found only an empty `frontend/main.tsx`; package metadata and source tree were absent, so the frontend needs a complete Vite scaffold.
- L10: Frontend verification: `npm install` completed with zero vulnerabilities and `npm run build` passed after adding Vite `ImportMeta` typings; 50 modules transformed successfully.
