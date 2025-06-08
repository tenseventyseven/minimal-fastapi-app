import pytest
from httpx import ASGITransport, AsyncClient

from minimal_fastapi_app.main import app


@pytest.mark.asyncio
async def test_create_project():
    project_data = {
        "name": "Project Alpha",
        "description": "A test project",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/projects/", json=project_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Project Alpha"
        assert data["description"] == "A test project"
        assert data["id"] == 1
        assert "created_at" in data
        assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
async def test_create_duplicate_project():
    project_data = {"name": "Project Alpha"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        await ac.post("/v1/projects/", json=project_data)
        response = await ac.post("/v1/projects/", json=project_data)
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"] == "business_error"
        assert "correlation_id" in error_data
        assert "name" in str(error_data["details"]).lower()
        assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
async def test_get_projects_empty():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/projects/")
        assert response.status_code == 200
        assert response.json()["items"] == []
        assert response.json()["total"] == 0
        assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
async def test_get_projects_with_pagination():
    for i in range(5):
        project_data = {"name": f"Project {i}"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            await ac.post("/v1/projects/", json=project_data)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/projects/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["skip"] == 2
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Project 2"
        assert data["items"][1]["name"] == "Project 3"


@pytest.mark.asyncio
async def test_get_project_by_id():
    project_data = {"name": "Specific Project", "description": "Desc"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        create_response = await ac.post("/v1/projects/", json=project_data)
        project_id = create_response.json()["id"]
        response = await ac.get(f"/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Specific Project"
        assert data["description"] == "Desc"


@pytest.mark.asyncio
async def test_get_nonexistent_project():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/projects/999")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
