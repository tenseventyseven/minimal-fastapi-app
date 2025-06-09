# Combined user-project relationship and association tests
import pytest
from httpx import ASGITransport, AsyncClient

from minimal_fastapi_app.main import app


# --- Association/Relationship Actions ---
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
        # Check user is in project
        users = (await ac.get(f"/v1/projects/{project_id}/users")).json()
        assert any(u["id"] == user_id for u in users)


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


# --- Listing/Querying Relationships ---
@pytest.mark.asyncio
async def test_list_users_in_project():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        user_data = {"name": "User1", "email": "user1@ex.com"}
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        project_data = {"name": "Proj1"}
        project_resp = await ac.post("/v1/projects/", json=project_data)
        project_id = project_resp.json()["id"]
        await ac.post(f"/v1/projects/{project_id}/users/{user_id}")
        resp = await ac.get(f"/v1/projects/{project_id}/users")
        assert resp.status_code == 200
        users = resp.json()
        assert any(u["id"] == user_id for u in users)


@pytest.mark.asyncio
async def test_list_projects_for_user():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        user_data = {"name": "User2", "email": "user2@ex.com"}
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["id"]
        project1 = (await ac.post("/v1/projects/", json={"name": "ProjA"})).json()
        project2 = (await ac.post("/v1/projects/", json={"name": "ProjB"})).json()
        await ac.post(f"/v1/projects/{project1['id']}/users/{user_id}")
        await ac.post(f"/v1/projects/{project2['id']}/users/{user_id}")
        resp = await ac.get(f"/v1/projects/user/{user_id}/projects")
        assert resp.status_code == 200
        projects = resp.json()
        project_names = [p["name"] for p in projects]
        assert "ProjA" in project_names and "ProjB" in project_names


@pytest.mark.asyncio
async def test_list_users_in_nonexistent_project():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/v1/projects/9999/users")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_projects_for_nonexistent_user():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/v1/projects/user/9999/projects")
        assert resp.status_code == 404
