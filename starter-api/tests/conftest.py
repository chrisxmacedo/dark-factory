import asyncio
import os
import subprocess

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from src.database import get_db
from src.main import app

# ── Required env vars ─────────────────────────────────────────────────────────
#
# These point to the shared ClauseHub test Supabase project.
# Each API project specifies its own TEST_SCHEMA to stay isolated.
#
# Add to .env:
#   SUPABASE_TEST_URL=postgresql+asyncpg://postgres:...@db.REF.supabase.co:5432/postgres
#   TEST_SUPABASE_JWT_SECRET=your-test-jwt-secret
#   TEST_SCHEMA=your_api_name   (e.g. clausehub_api)

TEST_DATABASE_URL = os.environ.get("SUPABASE_TEST_URL")
TEST_SCHEMA = os.environ.get("TEST_SCHEMA")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "SUPABASE_TEST_URL is not set.\n"
        "This should point to the shared ClauseHub test Supabase project.\n"
        "Add it to your .env — see docs/HUMAN_GUIDE.md for setup instructions."
    )

if not TEST_SCHEMA:
    raise RuntimeError(
        "TEST_SCHEMA is not set.\n"
        "Set it to a unique schema name for this project (e.g. clausehub_api).\n"
        "Add TEST_SCHEMA=your_api_name to your .env."
    )

# Normalise URL driver
if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif TEST_DATABASE_URL.startswith("postgres://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


# ── Migration helpers ─────────────────────────────────────────────────────────


def run_alembic(command: list[str]) -> None:
    """Run an alembic command against the test schema."""
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["DB_SCHEMA"] = TEST_SCHEMA
    result = subprocess.run(
        ["uv", "run", "alembic", *command],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Alembic command failed: {' '.join(command)}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


# ── Session-scoped fixtures ───────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def migrate_test_db():
    """
    Drop and recreate the test schema, then run all migrations.
    Runs once per test session — fast, clean, and catches migration errors.
    """
    print(f"\n▶ Resetting test schema: {TEST_SCHEMA}")

    # Drop and recreate schema using a synchronous engine
    import sqlalchemy as sa
    sync_url = TEST_DATABASE_URL.replace("+asyncpg", "")
    engine = sa.create_engine(sync_url)
    with engine.connect() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
        conn.execute(text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))
        conn.commit()
    engine.dispose()
    print(f"  ✓ Schema {TEST_SCHEMA} recreated")

    run_alembic(["upgrade", "head"])
    print("  ✓ Migrations applied")
    yield


@pytest_asyncio.fixture(scope="session")
async def test_engine(migrate_test_db):
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"server_settings": {"search_path": TEST_SCHEMA}},
    )
    yield engine
    await engine.dispose()


# ── Function-scoped fixtures ──────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Each test gets a transaction that rolls back on completion —
    so tests never affect each other.
    """
    async with test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Async HTTP client with db dependency overridden to the test session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Auth helpers ──────────────────────────────────────────────────────────────


def make_jwt(
    sub: str = "00000000-0000-0000-0000-000000000001",
    email: str = "test@example.com",
    role: str = "authenticated",
    expired: bool = False,
    wrong_secret: bool = False,
) -> str:
    """Generate a test JWT signed with the test Supabase JWT secret."""
    import time
    from jose import jwt

    secret = os.environ.get("TEST_SUPABASE_JWT_SECRET", "")
    if wrong_secret:
        secret = "wrong-secret"

    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "iat": now - 3600 if expired else now,
        "exp": now - 1 if expired else now + 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt()}"}


@pytest.fixture
def expired_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(expired=True)}"}


@pytest.fixture
def wrong_secret_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(wrong_secret=True)}"}
