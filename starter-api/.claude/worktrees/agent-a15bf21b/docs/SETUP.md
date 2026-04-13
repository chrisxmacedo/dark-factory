# AI Agent Setup — starter-api

This file is read by Claude Code agents when setting up a new instance of
this project. Follow these steps exactly.

---

## 1. Install dependencies

```bash
uv sync
```

---

## 2. Configure environment

```bash
cp .env.example .env
```

Fill in all values in `.env`. If setting up as part of `/create-project`,
these values were already written automatically — verify they are present.

---

## 3. Apply database migrations

```bash
uv run alembic upgrade head
```

If this fails, check that `DATABASE_URL` in `.env` is correct and that the
Supabase project has finished provisioning.

---

## 4. Verify the setup

```bash
uv run uvicorn src.main:app --reload &
sleep 2
curl -sf http://localhost:8000/health && echo "✓ API is running"
```

---

## 5. Run the full CI check

```bash
uv run ruff check . && \
uv run ruff format --check . && \
uv run mypy src/ && \
uv run pytest
```

All checks must pass before starting any work.

---

## 6. Read CLAUDE.md

Read `CLAUDE.md` in the repo root before writing any code. It contains the
conventions all agents must follow.

---

## 7. Read PRD.md and PLAN.md (if they exist)

If this is a project generated from `starter-api` (not the template itself),
`PRD.md` and `PLAN.md` will exist in the repo root. Read both before starting
any ticket — they define what this API does and how it should behave.
