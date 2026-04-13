# CLAUDE.md — {project-name}-api

This file covers coding conventions for this API repo. For project-wide
architecture, service providers, and secrets, see `../CLAUDE.md` and
`../.secrets.md` in the parent project directory.

<!-- When creating a new project from starter, you MUST also create the
     parent-level files. See docs/PROJECT_SETUP.md for the templates. -->

---

## Stack

- **Python 3.12**, FastAPI, SQLAlchemy (async), Alembic, Supabase Auth
- **Package manager:** uv (`uv sync`, `uv run`, `uv add`)
- **Linting/formatting:** ruff
- **Type checking:** mypy (strict)
- **Testing:** pytest + httpx + factory-boy

---

## Project structure

```
src/
├── main.py           # App factory, middleware, router registration
├── config.py         # Settings (pydantic-settings, reads .env)
├── database.py       # SQLAlchemy engine + session + Base
├── dependencies.py   # Shared FastAPI dependency type aliases
├── middleware/
│   ├── auth.py       # Supabase JWT verification + CurrentUser
│   └── logging.py    # Structured request logging
├── routers/          # One file per resource (health.py, users.py, etc.)
└── models/           # SQLAlchemy ORM models (one file per table)

tests/
├── conftest.py       # Fixtures: test engine, db session, async client
├── factories.py      # factory-boy factories for test data
└── test_*.py         # Tests — one file per router

alembic/
└── versions/         # Auto-generated migration files — never edit manually
```

---

## Conventions

### General
- All functions must have full type annotations
- All module-level code must be importable without side effects
- Never use `print()` — use `structlog.get_logger()` instead
- Never hardcode secrets or URLs — always read from `get_settings()`
- Never commit `.env` — use `.env.example` as the reference

### Routers
- One router file per resource in `src/routers/`
- Register the router in `src/main.py` with a `prefix`
- Always specify `response_model`, `status_code`, `summary` on every endpoint
- Use `DB` and `RequireAuth` from `src/dependencies.py` for dependencies

### Models
- One SQLAlchemy model per file in `src/models/`
- Export all models from `src/models/__init__.py`
- Always include `id`, `created_at`, `updated_at` on every table
- Use `UUID` primary keys

### Schemas (Pydantic)
- Define request/response schemas in the router file (or a `schemas/` file
  for complex resources)
- Always use separate `Create`, `Update`, and `Response` schemas
- Never expose SQLAlchemy model objects directly in responses

### API design principles

These principles guide all resource and endpoint design decisions.

**Domain-aligned schemas**
- Schemas must reflect real-world domain structures, not database internals
- Avoid "mega-schemas" — if a resource has logically distinct sections,
  decompose them into focused schemas
- Name fields using domain language, not implementation terms

**Sub-resource decomposition**
- If part of a resource varies independently, model it as a sub-resource:
  ```
  /products/{id}/fees
  /products/{id}/eligibility
  /products/{id}/documents
  ```
- Each sub-resource gets its own model, schemas, and CRUD endpoints
- Router file: `src/routers/{parent}_{sub}.py` (e.g. `products_fees.py`)
- Sub-resource endpoints are registered under the parent's prefix
- Rule: if data can be created, updated, or listed independently → sub-resource

**Repeating patterns across resource types**
- Common sub-resource shapes (fees, tiers, eligibility, features) should use
  shared base schemas and follow identical URL structures across parent types
- Define shared base schemas in `src/schemas/` (e.g. `fee_base.py`) and
  extend per resource type when needed

**Owner scoping**
- Every resource must have an `owner_id` (or domain-appropriate equivalent
  like `bank_id`, `org_id`)
- All write endpoints must verify `current_user` owns the resource
- List endpoints must filter to the authenticated user's resources by default
- Never allow cross-owner reads unless explicitly designed as a public or
  comparison endpoint

**Data lifecycle separation**
- Keep ingestion (creating/importing data), management (owner editing), and
  consumption (read-only querying/comparison) as distinct concerns
- Comparison or aggregation endpoints are always read-only and live under a
  separate prefix (e.g. `/comparison`, `/search`)
- Consumption endpoints may use denormalised views or cached data

**Single API surface**
- One API serves all resource types — do not create separate APIs per type
- Use top-level prefixes to namespace resource types:
  ```
  /products/mortgages
  /products/savings-accounts
  ```
- Each resource type has its own schema but shares middleware, auth, envelopes,
  and error conventions

---

### Migrations
- Generate with: `uv run alembic revision --autogenerate -m "description"`
- Apply with: `uv run alembic upgrade head`
- **Always run `uv run alembic upgrade head` before starting the dev server**
  after any schema change -- missing migrations crash the API at startup
- Never edit migration files after they have been applied to any environment
- Never delete migration files

### Auth
- Use `RequireAuth` from `src/dependencies.py` to protect endpoints
- Public endpoints (no auth needed) must be explicitly documented as such
- Never trust user-supplied IDs — always use `current_user.id` from the token

### Testing
- Every new endpoint needs at least one test
- Use `UserFactory` (and add new factories as needed) for test data
- Use the `client` fixture from `conftest.py` for all HTTP tests
- Test both success and error cases
- Tests must not depend on each other or on execution order

---

## Common commands

```bash
uv sync                               # Install dependencies
uv run uvicorn src.main:app --reload  # Start dev server
uv run pytest                         # Run tests
uv run ruff check .                   # Lint
uv run ruff format .                  # Format
uv run mypy src/                      # Type check
uv run alembic upgrade head           # Apply migrations
uv run alembic revision --autogenerate -m "description"  # New migration
```

---

## Versioned models

For any resource that requires audit history or regulatory compliance,
use the immutable versioning pattern instead of standard CRUD.

### When to use versioning

Use `VersionedMixin` when:
- The resource has regulatory significance (prices, contracts, rates)
- Consumers need point-in-time queries ("what was the rate on date X?")
- Changes must be auditable (who changed what, when)
- Hard deletes are not acceptable

### Model definition

```python
import uuid
from sqlalchemy import String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.versioned import VersionedMixin

class Tariff(VersionedMixin, Base):
    __tablename__ = "tariffs"

    # Stable identity across versions
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Resource-specific fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
```

### Repository usage

```python
from src.repositories.versioned import VersionedRepository

class TariffRepository(VersionedRepository[Tariff, CreateTariffRequest]):
    async def create(self, data: CreateTariffRequest, user_id: uuid.UUID) -> Tariff:
        return await self.create_version(
            resource_id=uuid.uuid4(),
            data=data,
            created_by=user_id,
            version_number=1,
        )

    async def update(self, resource_id: uuid.UUID, data: UpdateTariffRequest, user_id: uuid.UUID) -> Tariff:
        current = await self.get_current(resource_id)
        if not current:
            raise HTTPException(status_code=404, ...)
        return await self.supersede(current=current, data=data, created_by=user_id)
```

### Router conventions

- `POST /resource` — creates version 1 (new resource)
- `PATCH /resource/{resource_id}` — creates version N+1 (supersedes current)
- `GET /resource/{resource_id}` — returns current version only
- `DELETE /resource/{resource_id}` — NOT SUPPORTED, return 405
- Version history endpoints are added via `create_version_router()`:

```python
from src.routers.versions import create_version_router

version_router = create_version_router(
    model=Tariff,
    response_schema=TariffResponse,
    prefix="/tariffs/{resource_id}",
    tags=["tariffs"],
)
app.include_router(version_router)
# Adds: GET /tariffs/{id}/versions
#       GET /tariffs/{id}/versions/{version_id}
#       GET /tariffs/{id}/versions/{v1}/diff/{v2}
#       GET /tariffs/{id}/at/{timestamp}
```

### Migration pattern

Every versioned model needs its own migration. Use this as a template:

```python
def upgrade() -> None:
    op.create_table(
        "tariffs",
        # Versioning columns (always the same)
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, index=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Resource-specific columns
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rate", sa.Numeric(10, 4), nullable=False),
    )
    # Composite index for fast current-version lookups
    op.create_index("ix_tariffs_resource_current", "tariffs", ["resource_id", "is_current"])
    # Index for point-in-time queries
    op.create_index("ix_tariffs_resource_valid_from", "tariffs", ["resource_id", "valid_from"])
```

---



This API is designed to be consumed by AI agents as well as humans. Follow
these conventions on every endpoint so agents can discover and operate the
API reliably.

### Required endpoint metadata

Every endpoint MUST include:

```python
@router.get(
    "/items/{id}",
    response_model=DataResponse[ItemResponse],  # always use envelope
    status_code=status.HTTP_200_OK,
    summary="Get item by ID",                   # short, imperative
    description=(
        "Returns a single item by ID. "
        "Include what agents need to know: when to call this, "
        "what it returns, any side effects."
    ),
    responses={
        200: {"description": "Item found"},
        404: {
            "description": "Item not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "not_found",
                            "message": "Item not found"
                        }
                    }
                }
            }
        }
    },
    openapi_extra={
        "x-agent-hints": {
            "idempotent": True,          # safe to retry?
            "auth_required": True,       # requires auth?
            "use_for": "...",            # when should an agent call this?
        }
    }
)
```

### Response envelopes

ALL endpoints must use the standard envelopes from `src/schemas/envelope.py`:

- Single resource → `DataResponse[T]`
- Collection → `CollectionResponse[T]` with pagination
- Error → `ErrorResponse` with machine-readable `code`

Never return raw dicts, bare lists, or custom response shapes.

### Error codes

Use these standard codes in `ErrorDetail.code`:

| Code | When to use |
|---|---|
| `not_found` | Resource does not exist |
| `validation_error` | Request body/params invalid |
| `unauthorized` | No valid auth token |
| `forbidden` | Authenticated but not permitted |
| `conflict` | Resource already exists |
| `rate_limited` | Too many requests |
| `internal_error` | Unexpected server error |

### Bulk operations

For any resource that agents might need to create/update in volume,
add a bulk endpoint following the pattern in `src/schemas/bulk.py`:

```
POST   /items/bulk   — BulkCreateRequest[CreateItemRequest] → BulkResponse[ItemResponse]
PATCH  /items/bulk   — BulkUpdateRequest[UpdateItemRequest] → BulkResponse[ItemResponse]
DELETE /items/bulk   — BulkDeleteRequest → BulkResponse[None]
```

Bulk endpoints always return 200 even on partial failure — check each
`BulkResult.success` field.

### Idempotency

All write endpoints automatically support idempotency via the
`Idempotency-Key` header (middleware in `src/middleware/idempotency.py`).
No per-endpoint changes needed — document it in the endpoint description.

### Pagination

All list endpoints must accept `page` and `page_size` query params and
return `CollectionResponse` with `meta` and `links`. Use `PaginationParams`
as a dependency:

```python
from src.schemas import CollectionResponse, PaginationParams
from fastapi import Depends, Request

@router.get("/items", response_model=CollectionResponse[ItemResponse])
async def list_items(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    db: DB,
    current_user: RequireAuth,
) -> CollectionResponse[ItemResponse]:
    items, total = await fetch_items(db, pagination.page, pagination.page_size)
    return CollectionResponse.paginate(
        data=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        base_url=str(request.url),
    )
```

---



Every API project has two auto-generated client libraries:
- `{repo-name}-client-py` — Python client
- `{repo-name}-client-ts` — TypeScript client

**How it works:**
1. On every merge to `main`, the `publish-clients.yml` workflow runs
2. It exports `openapi.json` using `scripts/export_openapi.py`
3. It triggers the `regenerate.yml` workflow in both client repos
4. Each client repo opens a PR with the regenerated code

**Never manually edit client repos** — all changes flow from the API source.

**To export the spec locally:**
```bash
uv run python scripts/export_openapi.py
```

---

## Before writing code

- Read existing files in the area being modified before generating any code
- If adding a new endpoint: read existing routers and schemas for conventions
- If modifying models: read the current model and its migration history
- Verify you are in the correct repo: `pwd && git remote get-url origin`

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest
```

---

## PRD and PLAN

If `PRD.md` and `PLAN.md` exist in the repo root, read them before starting
any ticket. They are the source of truth for what this API does and how it
should behave. All endpoint design decisions must align with the PRD.
