# Pharmacy Inventory and Expiration Control

Incremental implementation of a pharmacy inventory system with batch-level expiration control, PEPS/FEFO stock rotation, alerts, and reports.

The backend is complete for use cases CU-01 through CU-13. Telegram, LLM, LangChain, and RAG integration (CU-14 through CU-16) is intentionally deferred and currently returns `501 Not Implemented`.

## Stack

- PostgreSQL 16 with pgvector (Docker, host port `5433`)
- FastAPI, SQLAlchemy 2, Pydantic v2
- Argon2 password hashing and JWT authentication
- React, TypeScript, and Vite

## Architecture

```
backend/app/
  api/v1/routers/     HTTP layer only
  services/           business rules and transactions
  repositories/       database queries
  models/             SQLAlchemy entities
  schemas/            Pydantic contracts
  core/               settings, database, security, dependencies, errors
backend/scripts/seed.py
backend/db/db.sql
frontend/src/
```

Dependency direction: `router -> service -> repository -> model`. Routers contain no SQL.

## Database

```bash
docker compose up -d db
```

Compose starts `pgvector/pgvector:pg16`, creates the `farmacias` database, and applies `backend/db/db.sql` on first initialization. The schema is guarded with `IF NOT EXISTS`, so it can also be applied manually.

The application connects to:

```
postgresql+psycopg://farmacias:farmacias@localhost:5433/farmacias
```

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m scripts.seed
uvicorn app.main:app --reload
```

- API docs: `http://localhost:8000/api/v1/docs`
- Health check: `http://localhost:8000/health`

Seeded credentials:

| Role | Email | Password |
| --- | --- | --- |
| Administrator | `admin@farmacia.com` | `Farmacia123` |
| Employee | `empleado@farmacia.com` | `Farmacia123` |

The seed is idempotent: running it again does not duplicate data.

## Tests

```bash
cd backend
python -m pytest tests -q
```

The suite uses SQLite in memory with a dependency override, so it does not require Docker. It covers authentication, catalog, inventory, PEPS allocation, alerts, reports, and administration. PostgreSQL-specific behavior such as `FOR UPDATE` locking remains to be verified against the live container.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server runs on `http://localhost:5173` and calls the API at `http://localhost:8000/api/v1` by default. Override it with `VITE_API_URL`.

## Implemented use cases

| Use case | Behavior |
| --- | --- |
| CU-01 | Login with JWT; account locks after 5 failed attempts for 15 minutes |
| CU-02 | Administrator user management with self-demotion guard |
| CU-03 | Branch management with duplicate-name conflicts |
| CU-04 | Medicine CRUD, logical deactivation, pagination via `X-Total-Count` |
| CU-05 | Barcode lookup with current stock and batch breakdown |
| CU-06 | Batch entry with past-date, supplier, and lot/expiration conflict validation |
| CU-07 | Sale or waste with PEPS, manual lot override plus reason, expired-lot protection, low-stock alerts |
| CU-08 | Inventory totals and per-lot breakdown, search by name or barcode |
| CU-09 | Kardex with lot, user, and date-range filters |
| CU-10 | Multiple expiration thresholds (for example 90, 60, 30 days) |
| CU-11 | Idempotent alerts job that also marks expired lots |
| CU-12 | Alerts enriched with medicine, lot, expiration, and quantity |
| CU-13 | Inventory, waste, expiring, and movement reports plus CSV export |

## Alerts job

The job is exposed for manual or scheduled execution:

```
POST /api/v1/alertas/generar   (Administrator only)
```

It creates expiration alerts without duplicating existing ones, marks expired batches, and returns the number of alerts created. Schedule it once per day with cron, Task Scheduler, or an external scheduler.

## Known limitations

- The Docker daemon was unavailable during development, so live PostgreSQL integration has not been executed yet. All behavior is verified with SQLite.
- Alembic is deferred while `db.sql` remains the schema baseline. Add a baseline revision once the live database is reachable.
- Telegram, LLM, and RAG endpoints return `501` by design.
