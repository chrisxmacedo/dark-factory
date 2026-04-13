# Async Python best practices

Read by: teams working on starter-api and any Python service with async I/O. Extends python.md and fastapi.md.

## async/await fundamentals

- All FastAPI route handlers must be `async def` — never plain `def` for endpoints that perform I/O
- Every I/O call (database, HTTP, file, queue) must use `await`
- Never call blocking functions inside an async context — they freeze the entire event loop

```python
# Correct
@router.get("/users/{user_id}")
async def get_user(user_id: uuid.UUID, db: DB) -> DataResponse[UserResponse]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    ...

# Wrong — blocks the event loop
@router.get("/users/{user_id}")
async def get_user(user_id: uuid.UUID, db: DB) -> DataResponse[UserResponse]:
    time.sleep(1)  # freezes all concurrent requests
    data = requests.get(f"https://api.example.com/users/{user_id}")  # blocking HTTP
    ...
```

## SQLAlchemy async

- Always use `AsyncSession` from `sqlalchemy.ext.asyncio` — never `Session`
- Use `async with session.begin()` for transactions that should auto-commit/rollback
- All queries go through `await session.execute()` — never call `.all()`, `.first()`, or `.one()` directly on a query object
- Lazy-loaded relationships will raise errors in async — use `selectinload()` or `joinedload()` eagerly

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_with_orders(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.orders))
    )
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, data: CreateUserRequest) -> User:
    async with session.begin():
        user = User(**data.model_dump())
        session.add(user)
    # auto-commits on exit, auto-rollbacks on exception
    await session.refresh(user)
    return user
```

## httpx for external calls

- Use `httpx.AsyncClient` for all external HTTP calls — never `requests`
- Share a single client instance per service via the app lifespan (connection pooling, keep-alive)
- Set explicit timeouts on every request — never rely on defaults

```python
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    yield
    await app.state.http_client.aclose()

# In a route or dependency
async def fetch_external_profile(request: Request, user_id: uuid.UUID) -> dict:
    client: httpx.AsyncClient = request.app.state.http_client
    response = await client.get(
        f"https://api.example.com/profiles/{user_id}",
        timeout=5.0,
    )
    response.raise_for_status()
    return response.json()
```

## Concurrent operations

Use `asyncio.gather()` when you need multiple independent I/O calls to run in parallel:

```python
import asyncio

async def get_dashboard(
    db: AsyncSession, http_client: httpx.AsyncClient, user_id: uuid.UUID,
) -> DashboardResponse:
    # These three calls run concurrently — total time = slowest call, not sum
    user, permissions, notifications = await asyncio.gather(
        get_user(db, user_id),
        get_permissions(db, user_id),
        fetch_notifications(http_client, user_id),
    )
    return DashboardResponse(user=user, permissions=permissions, notifications=notifications)
```

For structured concurrency with automatic cancellation on failure (Python 3.11+), prefer `asyncio.TaskGroup`:

```python
async def sync_all_providers(
    db: AsyncSession, http_client: httpx.AsyncClient, provider_ids: list[uuid.UUID],
) -> list[SyncResult]:
    results: list[SyncResult] = []
    async with asyncio.TaskGroup() as tg:
        for pid in provider_ids:
            tg.create_task(sync_provider(db, http_client, pid, results))
    # If ANY task raises, all others are cancelled and the exception propagates
    return results
```

Key difference: `gather()` runs everything to completion even if one fails (unless you pass `return_exceptions=False` and handle the first exception). `TaskGroup` cancels all remaining tasks on the first unhandled exception — safer for operations that should either all succeed or all fail.

## Common mistakes

| Mistake | Fix |
|---|---|
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `open("file.txt")` | `async with aiofiles.open("file.txt")` or run in executor |
| `requests.get(url)` | `await http_client.get(url)` |
| `json.loads(big_file.read())` | Read with `aiofiles`, or use `await asyncio.to_thread(...)` |
| Forgetting `await` on a coroutine | Coroutine is created but never executes — no error, no result |
| Mixing sync `Session` and async `AsyncSession` | Pick one — async routes must use `AsyncSession` exclusively |
| Calling `session.commit()` (sync) in async code | Use `await session.commit()` or `async with session.begin()` |

When you must call a blocking function (e.g. CPU-heavy computation, a sync-only library), offload it to a thread:

```python
import asyncio

result = await asyncio.to_thread(blocking_function, arg1, arg2)
```

## Background tasks

Use FastAPI `BackgroundTasks` for lightweight fire-and-forget work that runs after the response is sent:

```python
from fastapi import BackgroundTasks

async def send_welcome_email(user_id: uuid.UUID, email: str) -> None:
    # This runs after the response is already sent to the client
    async with httpx.AsyncClient() as client:
        await client.post("https://email.example.com/send", json={...})

@router.post("/users", status_code=201)
async def create_user(
    data: CreateUserRequest, db: DB, background_tasks: BackgroundTasks,
) -> DataResponse[UserResponse]:
    user = await save_user(db, data)
    background_tasks.add_task(send_welcome_email, user.id, user.email)
    return DataResponse(data=UserResponse.model_validate(user))
```

For longer-lived tasks that need monitoring, use `asyncio.create_task()` with error handling:

```python
import asyncio
import structlog

log = structlog.get_logger()

async def long_running_sync(session_factory, job_id: uuid.UUID) -> None:
    try:
        async with session_factory() as session:
            await process_job(session, job_id)
    except Exception:
        log.exception("background_task_failed", job_id=str(job_id))

# In a route or lifespan
task = asyncio.create_task(long_running_sync(session_factory, job_id))
task.add_done_callback(lambda t: t.result() if not t.cancelled() else None)
```

Keep a reference to tasks created with `create_task()` — if the reference is garbage-collected, the task may be silently cancelled.

## Testing async code

Use `pytest-asyncio` with mode `auto` (set in `pyproject.toml` or `conftest.py`) so every async test function runs automatically:

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Write async test functions and fixtures:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()

@pytest.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: async_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

async def test_create_user(client: AsyncClient) -> None:
    response = await client.post("/users", json={"email": "test@example.com", "name": "Test"})
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["email"] == "test@example.com"

async def test_get_user_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/users/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
```

For testing code that uses `asyncio.gather()` or `TaskGroup`, test both the happy path and partial-failure scenarios:

```python
async def test_dashboard_partial_failure(client: AsyncClient, mocker) -> None:
    mocker.patch("src.services.fetch_notifications", side_effect=httpx.HTTPStatusError(...))
    response = await client.get("/dashboard")
    assert response.status_code == 502  # or however you handle upstream failures
```

NEVER:
- Use `def` route handlers that perform I/O — FastAPI runs them in a threadpool, wasting resources and losing async benefits
- Call `requests`, `urllib`, or any sync HTTP library inside async code
- Use `time.sleep()` in async code — it blocks the entire event loop
- Access lazy-loaded SQLAlchemy relationships without eager loading in async sessions
- Fire off `asyncio.create_task()` without storing the reference and handling errors
- Use `asyncio.gather(return_exceptions=True)` without checking each result for exceptions
