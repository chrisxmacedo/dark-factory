# starter-api

A FastAPI starter template for ClauseHub projects. Fork this to start a new
API — Supabase auth, SQLAlchemy, Alembic, structured logging, rate limiting,
and a full CI pipeline all pre-wired.

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| Language | Python 3.12 (strict mypy) |
| Database | Supabase (Postgres) |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Auth | Supabase JWT middleware |
| Logging | structlog (JSON) |
| Rate limiting | slowapi |
| Testing | pytest + httpx + factory-boy |
| Linting | ruff |
| Deployment | DigitalOcean App Platform |

## Getting started

See `docs/HUMAN_GUIDE.md` for full setup instructions.

```bash
uv sync
cp .env.example .env   # fill in your Supabase credentials
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

## Project structure

```
src/
├── main.py           # App factory, middleware, routers
├── config.py         # Settings from environment
├── database.py       # SQLAlchemy engine + session
├── dependencies.py   # Shared dependency aliases (DB, RequireAuth)
├── middleware/       # Auth + logging middleware
├── routers/          # One file per resource
└── models/           # SQLAlchemy ORM models
tests/
alembic/              # Migrations
.do/app.yaml          # DigitalOcean App Platform spec
```

## CI

Every PR runs: `ruff check` → `ruff format` → `mypy` → `pytest`

## Conventions

See `CLAUDE.md` for the full conventions guide used by both humans and
Claude Code agents.
