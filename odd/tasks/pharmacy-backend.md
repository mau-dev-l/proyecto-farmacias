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
- T7 (S1): inline — add characterization tests and align backend to router/service/repository layers — status: completed — commit: n/a (no Git repository)
- T8 (S1): inline — implement CU-04 through CU-09: pagination, enriched barcode lookup, entry validations, sale/waste PEPS with manual override, inventory breakdown, kardex filters — status: completed — commit: n/a (no Git repository)
- T9 (S1): inline — implement CU-10 through CU-13: multiple alert thresholds, idempotent alerts job, enriched alerts, detailed reports and CSV export — status: completed — commit: n/a (no Git repository)
- T10 (S1-S2): inline — add idempotent schema, development seed, and project README — status: completed — commit: n/a (no Git repository)

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
- L11: T7 verification: 26 tests passed (including 4 pure PEPS tests), compileall passed, routers contain no direct SQL, and the application still registers 30 routes. Characterization tests use SQLite in memory; PostgreSQL integration remains pending until Docker is available.
- L12: T7 fixed a portability bug: expiring-lot days remaining is calculated in Python instead of relying on PostgreSQL date subtraction.
- L13: T7 fixed a refactor regression: repository `flush()` calls were moved out of create paths so unique conflicts still map to HTTP 409.
- L14: T8 verification: 43 tests passed. Entry rejects past expiration dates, unknown suppliers, and same lot number with a different expiration date. Sales exclude expired lots; waste consumes them first. Manual lot override requires a reason. Low-stock alerts are deduplicated per medicine.
- L15: T9 verification: 51 tests passed. Alert configuration stores multiple thresholds, the alerts job is idempotent and marks expired lots, alerts include medicine/lot context, and reports support per-medicine waste grouping plus CSV export.
- L16: T10 verification: the seed ran twice against SQLite and created data only on the first run; `db.sql` now uses guarded types, tables, and indexes. Alembic remains deferred until a live PostgreSQL instance is available.
