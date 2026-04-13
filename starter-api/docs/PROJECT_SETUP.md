# Project Setup — Parent Directory Files

When creating a new project from starter-api, you must create two files in the
**parent project directory** (the folder that contains all the project's repos).

```
{project-name}/              ← parent directory
├── CLAUDE.md                ← architecture docs (create from template below)
├── .secrets.md              ← actual secret values (create from template below)
├── {project-name}-api/      ← this repo
├── {project-name}-api-client-py/
└── {project-name}-api-client-ts/
```

The parent `CLAUDE.md` is what Claude Code reads when working across repos.
Individual repos point up to it for architecture context and keep only their
repo-specific coding conventions.

---

## Template: CLAUDE.md

Create this at `{project-name}/CLAUDE.md`:

```markdown
# CLAUDE.md — {Project Name}

This file describes the {Project Name} project architecture. Read it before
working in any repo.

For secrets and credentials, see [.secrets.md](.secrets.md).

---

## What {Project Name} is

<!-- Describe what the project does in 2-3 sentences: who uses it, what data
     it manages, and any regulatory or compliance context. -->

---

## Repository map

| Repo | Purpose | Tech |
|---|---|---|
| `{project}-api` | Core backend | FastAPI, Python 3.12, SQLAlchemy async |
| `{project}-api-client-py` | Auto-generated Python client | openapi-python-client, httpx |
| `{project}-api-client-ts` | Auto-generated TypeScript client | openapi-typescript, openapi-fetch |

Client libraries are auto-generated — never edit them directly.

### Service dependency graph

<!-- Draw an ASCII diagram showing how repos and services connect. -->

---

## Service providers

<!-- For each provider, document:
     - Purpose (what it does for this project)
     - Region / project ref / identifiers (non-secret)
     - Dashboard URL
     - Which env vars hold its credentials
     Actual secret values go in .secrets.md, NOT here. -->

### Supabase — Database & Authentication
- **Purpose**: PostgreSQL database + JWT auth + user management
- **Region**:
- **Project ref**:
- **Dashboard**:
- **Auth URL**:
- **Env vars**: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`

### Fly.io — Hosting & Deployment
- **Purpose**: Container hosting
- **Org**: | **App**:
- **URL**:
- **Region**:
- **Deploy**: GitHub Actions → `flyctl deploy --remote-only --strategy rolling`
- **Env vars**: `FLY_ORG`, `FLY_APP`, `FLY_API_TOKEN` (GitHub secret)

### Sentry — Error Tracking
- **Purpose**: Exception tracking and alerting
- **Org / Project ID**:
- **Env vars**: `SENTRY_DSN`

### Axiom — Observability
- **Purpose**: Structured logging and metrics
- **Dataset**:
- **Env vars**: `AXIOM_TOKEN`, `AXIOM_DATASET`, `OTEL_SERVICE_NAME`

### Upstash — Redis Cache
- **Purpose**: Rate limiting, idempotency key caching
- **REST URL**:
- **Env vars**: `REDIS_URL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

<!-- Add additional providers as needed (Cloudflare, Checkly, Stripe, etc.) -->

---

## Authentication flow

1. Client calls `POST /auth/login` with email + password
2. Supabase Auth validates and returns a JWT access token
3. Client sends `Authorization: Bearer <token>` on subsequent requests
4. API verifies via ES256 (JWKS) with HS256 fallback
5. Token payload: `sub` (user ID), `email`, `role`, plus custom claims

### Roles

| Role | Access |
|---|---|
| `admin` | Full access |
| <!-- role --> | <!-- access --> |

---

## Inter-service communication

| From | To | Auth |
|---|---|---|
| Client libraries | API | Bearer token |
| GitHub Actions (CI) | Fly.io | `FLY_API_TOKEN` |
| GitHub Actions (publish) | Client repos | `CLIENTS_PAT` |

**CORS origins**: `http://localhost:3000`

---

## Test environment

- Shared test Supabase project (separate from production)
- Unique `TEST_SCHEMA` per API
- Tests run in transactions that roll back — no cross-test state

---

## Secrets reference

All secrets and API keys are documented in [.secrets.md](.secrets.md).
That file must never be committed. It references:

- `{project}-api/.env` — application secrets
- `{project}-api/.env.infrastructure` — infrastructure credentials
- GitHub repo secrets — deployment tokens
```

---

## Template: .secrets.md

Create this at `{project-name}/.secrets.md`:

```markdown
# Secrets Reference — {Project Name}

This file must never be committed. It documents actual secret values for local
development and operations.

---

## {project}-api/.env — Application secrets

\```
DATABASE_URL=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
SENTRY_DSN=
AXIOM_TOKEN=
AXIOM_DATASET=
OTEL_SERVICE_NAME=
REDIS_URL=
\```

---

## {project}-api/.env.infrastructure — Infrastructure credentials

\```
FLY_ORG=
FLY_APP=
\```

<!-- Add provider-specific credentials as provisioned -->

---

## GitHub repository secrets

| Secret | Purpose |
|---|---|
| `FLY_API_TOKEN` | Fly.io deployment |
| `CLIENTS_PAT` | Trigger client library regeneration |

---

## Test environment

\```
SUPABASE_TEST_URL=
TEST_SUPABASE_JWT_SECRET=
TEST_SCHEMA=
\```
```
