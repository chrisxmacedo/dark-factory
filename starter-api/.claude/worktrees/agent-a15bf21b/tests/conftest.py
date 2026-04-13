import os
import subprocess

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.database import get_db
from src.main import app

TEST_DATABASE_URL = os.environ.get("SUPABASE_TEST_URL")
TEST_SCHEMA = os.environ.get("TEST_SCHEMA")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "SUPABASE_TEST_URL is not set.\n"
        "Set it to a PostgreSQL connection string for tests."
    )

if not TEST_SCHEMA:
    raise RuntimeError(
        "TEST_SCHEMA is not set.\n"
        "Set it to a unique schema name (e.g. starter_api_test)."
    )

if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
elif TEST_DATABASE_URL.startswith("postgres://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace(
        "postgres://", "postgresql+asyncpg://", 1
    )


def run_alembic(command: list[str]) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL  # type: ignore[assignment]
    env["DB_SCHEMA"] = TEST_SCHEMA  # type: ignore[assignment]
    result = subprocess.run(
        ["uv", "run", "alembic", *command],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Alembic command failed: {' '.join(command)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


@pytest.fixture(scope="session", autouse=True)
def migrate_test_db() -> None:
    import sqlalchemy as sa

    sync_url = TEST_DATABASE_URL.replace("+asyncpg", "")  # type: ignore[union-attr]
    engine = sa.create_engine(sync_url)
    with engine.connect() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
        conn.execute(text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))
        conn.commit()
    engine.dispose()
    run_alembic(["upgrade", "head"])


@pytest_asyncio.fixture
async def db_session(migrate_test_db: None) -> AsyncSession:  # type: ignore[misc]
    engine = create_async_engine(
        TEST_DATABASE_URL,  # type: ignore[arg-type]
        echo=False,
        pool_pre_ping=True,
        connect_args={"server_settings": {"search_path": TEST_SCHEMA}},
    )
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:  # type: ignore[misc]
    from slowapi.middleware import SlowAPIMiddleware

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    original_middleware = app.user_middleware.copy()
    app.user_middleware = [
        m
        for m in app.user_middleware
        if getattr(m, "cls", None) is not SlowAPIMiddleware
    ]
    app.middleware_stack = app.build_middleware_stack()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    app.user_middleware = original_middleware
    app.middleware_stack = app.build_middleware_stack()


ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"
SUPPLIER_USER_ID = "00000000-0000-0000-0000-000000000002"
CONSUMER_USER_ID = "00000000-0000-0000-0000-000000000003"
TEST_SUPPLIER_ID = "00000000-0000-0000-0000-aaaaaaaaaaaa"


def make_jwt(
    sub: str = ADMIN_USER_ID,
    email: str = "test@example.com",
    role: str = "admin",
    supplier_id: str | None = None,
    expired: bool = False,
    wrong_secret: bool = False,
) -> str:
    import time

    from jose import jwt

    secret = os.environ.get("TEST_SUPABASE_JWT_SECRET", "")
    if wrong_secret:
        secret = "wrong-secret"

    now = int(time.time())
    payload: dict[str, object] = {
        "sub": sub,
        "email": email,
        "role": role,
        "iat": now - 3600 if expired else now,
        "exp": now - 1 if expired else now + 3600,
    }
    if supplier_id:
        payload["supplier_id"] = supplier_id
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(role='admin')}"}


@pytest.fixture
def supplier_headers() -> dict[str, str]:
    token = make_jwt(
        sub=SUPPLIER_USER_ID,
        role="supplier",
        supplier_id=TEST_SUPPLIER_ID,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def consumer_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {make_jwt(sub=CONSUMER_USER_ID, role='consumer')}"
    }


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt()}"}


@pytest.fixture
def expired_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(expired=True)}"}


@pytest.fixture
def wrong_secret_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(wrong_secret=True)}"}
