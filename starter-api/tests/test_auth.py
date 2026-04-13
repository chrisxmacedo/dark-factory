"""
Tests for the Supabase JWT auth middleware.

These tests verify the auth middleware in isolation by hitting a protected
endpoint. The /health endpoint is public — we test auth against a dedicated
test-only protected endpoint defined below, or you can replace with any
authenticated endpoint once your project has them.
"""

import pytest
from httpx import AsyncClient

from src.main import app
from src.dependencies import RequireAuth
from fastapi import APIRouter
from fastapi.responses import JSONResponse

# ── Test-only protected endpoint ──────────────────────────────────────────────
# Registered only during tests to give the auth middleware something to hit.

_test_router = APIRouter()


@_test_router.get("/_test/protected")
async def protected_endpoint(current_user: RequireAuth) -> JSONResponse:
    return JSONResponse({
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
    })


app.include_router(_test_router)

# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """A valid JWT should return 200 with the user payload."""
    response = await client.get("/_test/protected", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "00000000-0000-0000-0000-000000000001"
    assert data["email"] == "test@example.com"
    assert data["role"] == "authenticated"


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient) -> None:
    """A request with no token should return 403."""
    response = await client.get("/_test/protected")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_with_expired_token(
    client: AsyncClient,
    expired_auth_headers: dict[str, str],
) -> None:
    """An expired JWT should return 401."""
    response = await client.get("/_test/protected", headers=expired_auth_headers)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower() or \
           "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_with_wrong_secret(
    client: AsyncClient,
    wrong_secret_headers: dict[str, str],
) -> None:
    """A JWT signed with the wrong secret should return 401."""
    response = await client.get("/_test/protected", headers=wrong_secret_headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_malformed_token(
    client: AsyncClient,
) -> None:
    """A malformed token string should return 401."""
    response = await client.get(
        "/_test/protected",
        headers={"Authorization": "Bearer this.is.not.a.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_wrong_scheme(
    client: AsyncClient,
) -> None:
    """Using Basic auth scheme instead of Bearer should return 403."""
    response = await client.get(
        "/_test/protected",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_health_endpoint_is_public(client: AsyncClient) -> None:
    """Health endpoint must remain publicly accessible — no token needed."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_jwt_sub_maps_to_user_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """The `sub` claim in the JWT must map to the user ID in the response."""
    response = await client.get("/_test/protected", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # sub from make_jwt() default
    assert data["id"] == "00000000-0000-0000-0000-000000000001"
