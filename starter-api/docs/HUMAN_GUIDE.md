# Human Developer Setup — starter-api

This guide gets you from zero to running the dev server locally.

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — `brew install uv`
- A Supabase project (see below)

---

## 1. Clone and install

```bash
git clone https://github.com/ClauseHub/{repo-name}.git
cd {repo-name}
uv sync
```

---

## 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env` with your Supabase credentials. You'll need:

| Variable | Where to find it |
|---|---|
| `DATABASE_URL` | Supabase → Project Settings → Database → Connection string (direct, not pooler) — change `postgresql://` to `postgresql+asyncpg://` |
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase → Project Settings → API → anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API → service_role key |
| `SUPABASE_JWT_SECRET` | Supabase → Project Settings → API → JWT Secret |

---

## 3. Run database migrations

```bash
uv run alembic upgrade head
```

---

## 4. Start the dev server

```bash
uv run uvicorn src.main:app --reload
```

API is running at: http://localhost:8000
OpenAPI docs at: http://localhost:8000/docs

---

## 5. Run the test suite

```bash
uv run pytest
```

---

## Useful commands

```bash
uv run ruff check .                   # Lint
uv run ruff format .                  # Format
uv run mypy src/                      # Type check
uv run alembic revision --autogenerate -m "description"  # New migration
uv run alembic upgrade head           # Apply migrations
uv run alembic downgrade -1           # Roll back one migration
```

---

## Test environment setup (one-time)

Tests run against a **shared ClauseHub test Supabase project**, isolated per
API using a dedicated Postgres schema. This means one test Supabase project
for the whole org — each API gets its own schema within it.

### First time only — shared test project

If this is the first API in the org, create the shared test Supabase project:

1. Go to https://supabase.com/dashboard and create a project named `clausehub-test`
2. Keep it in the ClauseHub org (`knxvkbznjlxslpkqegkl`)
3. Note the project ref (from the URL)

Get the credentials from Project Settings → API:

| Variable | Where to find it |
|---|---|
| `SUPABASE_TEST_URL` | Database → Connection string (direct) — change `postgresql://` to `postgresql+asyncpg://` |
| `TEST_SUPABASE_JWT_SECRET` | API → JWT Secret |

These are **org-level** — the same values are used by every API project.
Store them once in GitHub org secrets at:
https://github.com/organizations/ClauseHub/settings/secrets/actions

### Per-project setup

Each API project needs a unique schema name. Add to your `.env`:

```bash
# Shared — same for all ClauseHub API projects
SUPABASE_TEST_URL=postgresql+asyncpg://postgres:password@db.REF.supabase.co:5432/postgres
TEST_SUPABASE_JWT_SECRET=your-shared-test-jwt-secret

# Unique to this project — choose a descriptive snake_case name
TEST_SCHEMA=your_api_name
```

Also set the app-level vars pointing at the test project:
```bash
SUPABASE_URL=https://TEST_REF.supabase.co
SUPABASE_ANON_KEY=your-test-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-test-service-role-key
SUPABASE_JWT_SECRET=your-shared-test-jwt-secret
DB_SCHEMA=your_api_name
```

### Running tests

```bash
uv run pytest
```

On each run the test suite:
1. Drops and recreates the schema (`TEST_SCHEMA`) in the shared test project
2. Runs all Alembic migrations against that schema
3. Wraps each test in a transaction that rolls back — tests never affect each other

### GitHub Actions secrets

| Secret | Scope | Value |
|---|---|---|
| `SUPABASE_TEST_URL` | Org-level | Shared test project connection string |
| `TEST_SUPABASE_JWT_SECRET` | Org-level | Shared test project JWT secret |
| `TEST_SUPABASE_APP_URL` | Org-level | Shared test project API URL |
| `TEST_SUPABASE_ANON_KEY` | Org-level | Shared test project anon key |
| `TEST_SUPABASE_SERVICE_ROLE_KEY` | Org-level | Shared test project service role key |
| `TEST_SCHEMA` | Repo-level | Unique schema name for this API |
