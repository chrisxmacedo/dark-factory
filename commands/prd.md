---
description: Generate a Product Requirements Document (PRD.md) and PLAN.md for a new API project or feature
---

# PRD: $ARGUMENTS

Generate a structured `PRD.md` and `PLAN.md` for a new API project or feature.
These documents become the source of truth for all subsequent development work.
All agents must read them before starting any ticket.

---

## CRITICAL — Step-by-step collaborative process

**Do NOT batch all questions at once or generate the full PRD in one go.**

Work through it one section at a time:

1. Ask the **Product** questions → wait for answers → confirm understanding
2. Ask the **Endpoints** questions → wait for answers → confirm understanding
3. Ask the **Auth & Access** questions → wait for answers → confirm understanding
4. Ask the **Technical** questions → wait for answers → confirm understanding
5. Present a **summary of all answers** → wait for user approval
6. Generate `PRD.md` → show it → wait for approval
7. Generate `PLAN.md` → show it → wait for approval
8. Offer to create tickets

At each step, pause and wait. If the user corrects anything, incorporate it
before moving on. Never assume — always confirm.

---

## Step 1 — Gather requirements (one section at a time)

### 1a — Product (ask these first, wait for answers)

1. **What does this API do?** (one sentence)
2. **Who consumes it?** (a web frontend, mobile app, third-party service, internal tooling, etc.)
3. **What problem does it solve?**
4. **Is this a new API or extending an existing one?**

### 1b — Endpoints (ask after Product, wait for answers)

5. **What are the core resource types?** (e.g. users, products, orders, sessions)
6. **What operations are needed per resource?** (list, get, create, update, delete, or custom actions)
7. **Are there any non-CRUD endpoints?** (e.g. search, export, webhooks, health, analytics)
8. **What does a typical request/response look like for the most important endpoint?**

### 1c — Auth & Access (ask after Endpoints, wait for answers)

9. **Is authentication required?** (yes / no / some endpoints public)
10. **What auth mechanism?** (Supabase JWT / API key / both)
11. **Are there multiple user roles?** If so, what are they and what can each do?
12. **Are there any rate limiting requirements?**

### 1d — Technical (ask after Auth, wait for answers)

13. **Are there any third-party integrations required?** (payment processors, email, storage, etc.)
14. **Are there background jobs or async tasks?** (e.g. sending emails, processing uploads)
15. **What are the performance expectations?** (requests per second, response time targets)
16. **Any specific compliance or data retention requirements?**

---

## Step 2 — Generate PRD.md

Write `PRD.md` in the project root.

```markdown
# PRD: {Product Name}

**Version:** 1.0
**Date:** {today}
**Status:** Draft

---

## Overview
{2-3 sentence description of what this API does and why it exists}

## Problem Statement
{What problem does this solve? Who experiences it?}

## Consumers
{Who/what calls this API? Be specific.}

---

## Endpoints

### Public endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — always required |
{list additional public endpoints}

### Authenticated endpoints
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
{list authenticated endpoints with required roles}

---

## Data Models

For each core resource, define the shape:

### {Resource}
```python
class {Resource}(BaseModel):
    id: uuid.UUID
    created_at: datetime
    {fields with types}
```

---

## Auth & Access

- **Mechanism:** {Supabase JWT / API key / both}
- **Public endpoints:** {list}
- **Roles:** {list roles and permissions, or "single role"}
- **Rate limiting:** {limits or "none"}

---

## Integrations
{List third-party services, or "None"}

## Background Tasks
{List async jobs, or "None"}

## Performance Targets
- Response time: {target}
- Throughput: {target or "no specific requirement"}

## Technical Requirements
- **Stack:** Python, FastAPI, SQLAlchemy, Alembic, Supabase (Postgres)
- **Deployment:** DigitalOcean App Platform
- **Python version:** 3.12+

---

## Success Criteria
- [ ] All endpoints listed above implemented
- [ ] Auth middleware correctly enforces access control
- [ ] All endpoints have request/response validation via Pydantic
- [ ] All endpoints have test coverage
- [ ] CI passing (ruff, mypy, pytest, build)
- [ ] `/health` endpoint returns 200
- [ ] OpenAPI docs available at `/docs`
```

---

## Step 3 — Generate PLAN.md

Break the project into sequenced tickets. Each ticket should be 2-4 hours of
work maximum. Write `PLAN.md` in the project root:

```markdown
# Plan: {Product Name}

Generated from PRD.md on {today}.
Each item maps to one GitHub issue on Mission Control.

## Phase 1 — Foundation
- Scaffold FastAPI project structure
- Configure SQLAlchemy + Alembic
- Set up initial database migration
- Add auth middleware (Supabase JWT verification)
- Add CI GitHub Actions workflow (ruff, mypy, pytest)

## Phase 2 — Core Endpoints
{endpoints in dependency order — data models before operations}

## Phase 3 — Integrations & Background Tasks
{third-party integrations, async jobs if any}

## Phase 4 — Launch Readiness
- Rate limiting
- Error handling review
- Performance testing
- Documentation review
```

---

## Step 4 — Offer to create tickets

Ask: "Shall I create all tickets from PLAN.md on Mission Control now?"

If yes, use `/create-ticket` to create each ticket in order, with full
descriptions and acceptance criteria generated from the PRD.

---

## Step 5 — Summary

```
PRD and plan generated

  PRD    : {path}/PRD.md
  Plan   : {path}/PLAN.md
  Tickets: {number} created on Mission Control

  Next step: Review PRD.md, then run /take-task to begin Phase 1.
```

---

## Rules

- Never skip the endpoints section — it is the core of an API PRD
- Auth model must be defined before any endpoint tickets are created
- PRD.md must be committed to the repo — it is read by all agents
- Every endpoint in the PRD gets at least one ticket in the plan
