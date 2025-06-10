import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_read_root(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello World"
    assert data["status"] == "running"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_app_info(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "debug" in data


@pytest.mark.asyncio
async def test_openapi_docs(app):
    """Test that OpenAPI docs are accessible"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/openapi.json")
    assert response.status_code == 200
