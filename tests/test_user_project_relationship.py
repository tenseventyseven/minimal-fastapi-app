# Combined user-project relationship and association tests
import uuid

import pytest
from httpx import ASGITransport, AsyncClient


# --- Association/Relationship Actions ---
@pytest.mark.asyncio
async def test_add_user_to_project(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create user with unique email
        user_data = {
            "user_id": f"userproj-{uuid.uuid4()}",
            "given_name": "User Project",
            "family_name": "Test",
            "email": f"userproj-{uuid.uuid4()}@example.com",
        }
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["user_id"]
        # Create project with unique project_id
        project_data = {"project_id": f"Project Beta {uuid.uuid4()}"}
        project_resp = await ac.post("/v1/projects/", json=project_data)
        project_id = project_resp.json()["id"]
        # Add user to project
        response = await ac.post(f"/v1/projects/{project_id}/users/{user_id}")
        assert response.status_code == 204
        # Check user is in project
        users = (await ac.get(f"/v1/projects/{project_id}/users")).json()
        assert any(u["user_id"] == user_id for u in users)


@pytest.mark.asyncio
async def test_remove_user_from_project(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create user and project with unique email and project_id
        user_data = {
            "user_id": f"userremove-{uuid.uuid4()}",
            "given_name": "User Remove",
            "family_name": "Test",
            "email": f"userremove-{uuid.uuid4()}@ex.com",
        }
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["user_id"]
        project_data = {"project_id": f"ProjRemove {uuid.uuid4()}"}
        project_resp = await ac.post("/v1/projects/", json=project_data)
        project_id = project_resp.json()["id"]
        # Add user to project
        await ac.post(f"/v1/projects/{project_id}/users/{user_id}")
        # Remove user from project
        resp = await ac.delete(f"/v1/projects/{project_id}/users/{user_id}")
        assert resp.status_code == 204
        # Confirm user is no longer in project
        users = (await ac.get(f"/v1/projects/{project_id}/users")).json()
        assert all(u["user_id"] != user_id for u in users)
        # Removing again should 404
        resp2 = await ac.delete(f"/v1/projects/{project_id}/users/{user_id}")
        assert resp2.status_code == 404


# --- Listing/Querying Relationships ---
@pytest.mark.asyncio
async def test_list_users_in_project(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        user_data = {
            "user_id": f"user1-{uuid.uuid4()}",
            "given_name": "User1",
            "family_name": "Test",
            "email": f"user1-{uuid.uuid4()}@ex.com",
        }
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["user_id"]
        project_data = {"project_id": f"Proj1 {uuid.uuid4()}"}
        project_resp = await ac.post("/v1/projects/", json=project_data)
        project_id = project_resp.json()["id"]
        await ac.post(f"/v1/projects/{project_id}/users/{user_id}")
        resp = await ac.get(f"/v1/projects/{project_id}/users")
        assert resp.status_code == 200
        users = resp.json()
        assert any(u["user_id"] == user_id for u in users)


@pytest.mark.asyncio
async def test_list_projects_for_user(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        user_data = {
            "user_id": f"user2-{uuid.uuid4()}",
            "given_name": "User2",
            "family_name": "Test",
            "email": f"user2-{uuid.uuid4()}@ex.com",
        }
        user_resp = await ac.post("/v1/users/", json=user_data)
        user_id = user_resp.json()["user_id"]
        project1_id = f"ProjA {uuid.uuid4()}"
        project2_id = f"ProjB {uuid.uuid4()}"
        project1 = (
            await ac.post("/v1/projects/", json={"project_id": project1_id})
        ).json()
        project2 = (
            await ac.post("/v1/projects/", json={"project_id": project2_id})
        ).json()
        await ac.post(f"/v1/projects/{project1['id']}/users/{user_id}")
        await ac.post(f"/v1/projects/{project2['id']}/users/{user_id}")
        resp = await ac.get(f"/v1/projects/user/{user_id}/projects")
        assert resp.status_code == 200
        projects = resp.json()
        project_ids = [p["project_id"] for p in projects]
        assert project1_id in project_ids and project2_id in project_ids


@pytest.mark.asyncio
async def test_list_users_in_nonexistent_project(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/v1/projects/9999/users")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_projects_for_nonexistent_user(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/v1/projects/user/9999/projects")
        assert resp.status_code == 404
