import pytest
from httpx import ASGITransport, AsyncClient

from minimal_fastapi_app.main import app


@pytest.mark.asyncio
async def test_add_user_to_project():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create user
        user_data = {
            "name": "User Project",
            "email": "userproj@example.com",
        }
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        # Create project
        project_data = {"name": "Project Beta"}
        project_resp = await ac.post("/v1/projects/", json=project_data)
        project_id = project_resp.json()["id"]
        # Add user to project
        response = await ac.post(f"/v1/projects/{project_id}/users/{user_id}")
        assert response.status_code == 204
        # Check user is in project (fetch project and check users)
        # (Assume a /v1/projects/{project_id}/users endpoint or similar is implemented)


@pytest.mark.asyncio
async def test_remove_user_from_project():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create user and project
        user_data = {
            "name": "User Remove",
            "email": "userremove@ex.com",
        }
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        project_data = {"name": "ProjRemove"}
        project_resp = await ac.post("/v1/projects/", json=project_data)
        project_id = project_resp.json()["id"]
        # Add user to project
        await ac.post(f"/v1/projects/{project_id}/users/{user_id}")
        # Remove user from project
        resp = await ac.delete(f"/v1/projects/{project_id}/users/{user_id}")
        assert resp.status_code == 204
        # Confirm user is no longer in project
        users = (await ac.get(f"/v1/projects/{project_id}/users")).json()
        assert all(u["id"] != user_id for u in users)
        # Removing again should 404
        resp2 = await ac.delete(f"/v1/projects/{project_id}/users/{user_id}")
        assert resp2.status_code == 404
