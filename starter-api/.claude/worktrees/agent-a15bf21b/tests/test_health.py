import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_no_auth_required(client: AsyncClient) -> None:
    """Health endpoint must be publicly accessible — no token needed."""
    response = await client.get("/health")
    assert response.status_code == 200
