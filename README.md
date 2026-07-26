# PSX Fertilizer Research Platform (pilot)

A single-sector (PSX Fertilizer) pilot of a PSX investment research platform: fundamentals,
market data, macro/geopolitical risk context and a compliance-gated AI signal layer. See
`docs/` in `backend/` for the compliance gate templates this project is built around.

**Compliance gate**: no PSX data license exists yet. `PUBLIC_LAUNCH_ENABLED`,
`PUBLIC_SIGNALS_ENABLED` and `COMMERCIAL_DATA_ENABLED` default to `false` and must stay that
way until `backend/docs/rights_matrix.template.md` is actually filled in and reviewed.

## Stack

- Frontend: Next.js 16 (App Router) + TypeScript + Tailwind v4 + Recharts
- Backend: FastAPI + SQLAlchemy 2.0 + Alembic, Postgres
- Local dev: Docker Compose (Postgres + backend + frontend), or run each service natively

## Running locally

### Option A — Docker Compose (requires Docker Desktop running)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000/health

### Option B — native (what this repo was verified against)

Backend:
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env     # point DATABASE_URL at your own Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Repo layout

```
frontend/    Next.js app — dashboard UI (sample data for now, see src/lib/mock-data.ts)
backend/     FastAPI app, SQLAlchemy models, Alembic migrations, ingestion/etl/scoring modules
backend/docs/  Compliance gate templates (rights matrix, source registry, editorial SOP, disclaimer)
```

## Status

Milestone 1 (foundation) complete: schema, API skeleton, feature-flag gate, dashboard UI on
sample data. See the plan this was built from for Milestones 2-8 (real data ingestion,
ratio engine, full company research pages, market data, screener, AI signal layer).
