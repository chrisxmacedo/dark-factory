# starter-api/

Python/FastAPI REST API service template. Copy this directory to bootstrap a new
API backend with SQLAlchemy, Alembic migrations, Supabase Auth, and structured
logging.

## Contents

- **CLAUDE.md** -- Coding conventions, API design principles, versioned models
- **Dockerfile** -- Multi-stage build (deps, builder, migrate, runner)
- **pyproject.toml** -- Dependencies and tool configuration (ruff, mypy, pytest)
- **.env.example** -- All common environment variables with placeholder values
- **.gitignore** -- Python + environment files
- **src/main.py** -- App factory, middleware, router registration
- **src/config.py** -- Settings (pydantic-settings, reads .env)
- **src/database.py** -- SQLAlchemy engine + session + Base
- **src/routers/** -- One file per resource (health.py, etc.)
- **src/models/** -- SQLAlchemy ORM models (one file per table)
- **src/middleware/** -- Auth (Supabase JWT) and structured request logging
- **alembic/** -- Migration configuration and versions directory
- **tests/** -- pytest + httpx + factory-boy test suite

## For agents

- Replace all `{PLACEHOLDER}` values with project-specific configuration before use.
- Run `uv sync` after replacing placeholder values in pyproject.toml.
- Always run `uv run alembic upgrade head` before starting the dev server.
- See `CLAUDE.md` for coding conventions and common commands.
