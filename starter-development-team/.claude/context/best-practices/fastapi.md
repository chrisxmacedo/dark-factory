# FastAPI best practices

Read by: teams working on starter-api and starter-ml projects. Extends python.md.

## Project structure

```
src/
  main.py              — app factory with lifespan
  config.py            — Pydantic settings from .env
  database.py          — SQLAlchemy async engine + session
  dependencies.py      — type aliases (DB, RequireAuth)
  middleware/           — auth, logging, idempotency, rate-limit
  routers/             — one file per resource
  models/              — one file per table
  schemas/             — Pydantic request/response schemas
  repositories/        — data access layer (optional)
tests/
  conftest.py          — fixtures (engine, session, client)
  factories.py         — factory-boy factories
  test_{resource}.py   — per-resource tests
alembic/
  versions/            — migration files
```

## App factory

- Use lifespan context manager for startup/shutdown
- Mount middleware in order: SlowAPI → CORS → logging → idempotency
- Global exception handler for unhandled errors
- Limiter: configured from settings (default 60/min)

## Routers

- One router per resource, mounted in main.py
- Every endpoint MUST have: `response_model`, `status_code`, `summary`, `description`
- Standard error codes: `not_found`, `validation_error`, `unauthorized`, `forbidden`, `conflict`, `rate_limited`

## Schemas

- Separate schemas: `CreateRequest`, `UpdateRequest`, `Response` per resource
- Never expose the SQLAlchemy model directly as a response
- Use `Field()` for validation: min_length, max_length, regex, ge, le
- Pagination: `page` and `page_size` params, return `{ data, meta: { total, page, page_size } }`
- Bulk operations: `BulkCreateRequest[T]`, `BulkUpdateRequest[T]`, max batch size

## Auth

- `RequireAuth` dependency via Depends: validates JWT, extracts user
- Supabase JWT verification with JWKS fallback
- `CurrentUser` Pydantic model: id, email, role
- Protected by default — explicitly mark public endpoints

## Database

- SQLAlchemy async with `AsyncSession`
- UUID primary keys: `id`, `created_at`, `updated_at` on every table
- Domain-aligned table names (snake_case plural)
- Indexes on frequently queried columns
- Versioned models: `VersionedMixin` for regulatory/audit resources

## Idempotency

- `Idempotency-Key` header middleware
- Cache responses for 24 hours
- Return cached response on duplicate key

## Logging

- structlog middleware: logs request_id, method, path, status_code, duration_ms
- Bind context per request: `structlog.contextvars.bind_contextvars(request_id=...)`

## Health

- `GET /health` returning `{ "status": "ok" }`
- Check database connection
- Fast — no heavy queries

## OpenAPI

- Every endpoint: `summary` (short), `description` (detailed)
- `x-agent-hints` in `openapi_extra`: `idempotent`, `auth_required`, `use_for`
- Response envelopes: `DataResponse[T]`, `CollectionResponse[T]`, `ErrorResponse`

## Migrations

- `alembic revision --autogenerate -m "description"`
- Review auto-generated migration before applying
- Never edit auto-generated code unless adding explicit data migration
- Support multi-schema (test schema via `TEST_SCHEMA` env var)

## Testing

- `pytest` with `pytest-asyncio` (mode: auto)
- `httpx.AsyncClient` for endpoint tests
- `factory-boy` factories for test data
- Test both success AND error cases per endpoint
- Fixtures in `conftest.py`: async engine, session, authenticated client

NEVER:
- Return SQLAlchemy model objects directly — always map to Pydantic schema
- Use sync database operations — always async
- Skip response_model on endpoints — it enforces the API contract
- Use `alembic downgrade` in production without a tested plan
