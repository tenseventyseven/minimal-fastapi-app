import pytest
from httpx import ASGITransport, AsyncClient

from minimal_fastapi_app.main import app


@pytest.mark.asyncio
async def test_read_root():
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
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_app_info():
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
async def test_openapi_docs():
    """Test that OpenAPI docs are accessible"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/docs")
        assert response.status_code == 200
        response = await ac.get("/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        paths = openapi_data["paths"]
        assert "/v1/users/" in paths
        assert "post" in paths["/v1/users/"]
        assert "get" in paths["/v1/users/"]
