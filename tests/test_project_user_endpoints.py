from fastapi.testclient import TestClient
from minimal_fastapi_app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_list_users_in_project():
    # Create user and project
    user_data = {"name": "User1", "email": "user1@ex.com"}
    user_resp = client.post("/v1/users/", json=user_data)
    user_id = user_resp.json()["id"]
    project_data = {"name": "Proj1"}
    project_resp = client.post("/v1/projects/", json=project_data)
    project_id = project_resp.json()["id"]
    # Add user to project
    client.post(f"/v1/projects/{project_id}/users/{user_id}")
    # List users in project
    resp = client.get(f"/v1/projects/{project_id}/users")
    assert resp.status_code == 200
    users = resp.json()
    assert any(u["id"] == user_id for u in users)


def test_list_projects_for_user():
    # Create user and two projects
    user_data = {"name": "User2", "email": "user2@ex.com"}
    user_resp = client.post("/v1/users/", json=user_data)
    user_id = user_resp.json()["id"]
    project1 = client.post("/v1/projects/", json={"name": "ProjA"}).json()
    project2 = client.post("/v1/projects/", json={"name": "ProjB"}).json()
    # Add user to both projects
    client.post(f"/v1/projects/{project1['id']}/users/{user_id}")
    client.post(f"/v1/projects/{project2['id']}/users/{user_id}")
    # List projects for user
    resp = client.get(f"/v1/projects/user/{user_id}/projects")
    assert resp.status_code == 200
    projects = resp.json()
    project_names = [p["name"] for p in projects]
    assert "ProjA" in project_names and "ProjB" in project_names


def test_list_users_in_nonexistent_project():
    resp = client.get("/v1/projects/9999/users")
    assert resp.status_code == 404


def test_list_projects_for_nonexistent_user():
    resp = client.get("/v1/projects/user/9999/projects")
    assert resp.status_code == 404
