from fastapi.testclient import TestClient

from minimal_fastapi_app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello World"
    assert data["status"] == "running"
    assert "timestamp" in data
    assert "version" in data


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_app_info():
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "debug" in data


def test_openapi_docs():
    """Test that OpenAPI docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200

    # Check that openapi schema includes our users endpoints
    openapi_data = response.json()
    paths = openapi_data["paths"]
    assert "/v1/users/" in paths
    assert "post" in paths["/v1/users/"]
    assert "get" in paths["/v1/users/"]
