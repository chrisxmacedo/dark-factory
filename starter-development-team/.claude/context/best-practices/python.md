# Python best practices

Read by: all teams working on Python starters (api, ml)

## Version and tooling

- Python 3.12+
- Package manager: uv (fast, replaces pip + venv)
- Formatter: `ruff format` (line length 88)
- Linter: `ruff check` (select E, F, I, N, W, UP, B, C4, PT)
- Type checker: `mypy --strict`

## Type hints

- All functions typed — parameters AND return type
- Use `from __future__ import annotations` for modern syntax
- Complex types: `dict[str, Any]`, `list[int]`, `Optional[str]` or `str | None`
- Use `TypeVar` and `Generic` for reusable typed containers
- Pydantic models for all data validation

## Functions and classes

- Async everywhere: `async def` for IO-bound functions
- Use `asyncio` for concurrency, not threading
- Prefer composition over inheritance
- Dataclasses or Pydantic models over plain dicts
- Context managers for resource management (`async with`)

## Error handling

- No bare `except:` — always catch specific exceptions
- Log and re-raise with context, or handle completely
- Custom exception classes for domain errors
- Never catch `Exception` silently

## Naming

- `snake_case` for variables, functions, modules, packages
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Prefix private methods/attributes with `_`
- File names: `snake_case.py`

## Data validation

- Pydantic for ALL external data: request bodies, config, queue messages
- Separate schemas: `CreateRequest`, `UpdateRequest`, `Response` — never reuse input as output
- Use `Field()` for validation rules (min_length, max_length, regex)
- Config via `pydantic_settings.BaseSettings` reading from .env

## Database

- SQLAlchemy async sessions, always use context managers
- UUID primary keys with `id`, `created_at`, `updated_at` on every table
- Alembic for migrations — auto-generate with `alembic revision --autogenerate`
- Review generated migrations before applying
- Never edit auto-generated migrations unless adding data migration logic

## Logging

- structlog for structured JSON logging — never `print()`
- Bind context: `log = log.bind(user_id=user_id, request_id=request_id)`
- Log levels: debug (dev detail), info (business events), warning (degraded), error (failures)

## Testing

- pytest with pytest-asyncio (mode: auto)
- factory-boy for test data factories
- httpx.AsyncClient for API testing
- Coverage: `pytest --cov=src`
- Fixtures in conftest.py — async engine, session, client

## Paths and strings

- `pathlib.Path` over `os.path`
- f-strings for formatting (not `.format()` or `%`)
- Raw strings for regex: `r"pattern"`

NEVER:
- Use `print()` in production code
- Use `os.system()` or `subprocess.call()` with user input (command injection)
- Import * from any module
- Use mutable default arguments (`def f(items=[])`)
- Catch and ignore exceptions
