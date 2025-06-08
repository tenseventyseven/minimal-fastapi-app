import pytest
from fastapi.testclient import TestClient

from minimal_fastapi_app.main import app
from minimal_fastapi_app.users.service import user_service

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the database before each test"""
    user_service.users.clear()
    user_service.user_counter = 1


def test_create_user():
    """Should create a user with valid data and return the user object."""
    user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}
    response = client.post("/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["age"] == 30
    assert data["id"] == 1
    assert "created_at" in data

    # Check that correlation ID is in response headers
    assert "X-Correlation-ID" in response.headers


def test_create_duplicate_email():
    """Should fail to create a user if the email already exists."""
    user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}

    # Create first user
    response = client.post("/v1/users/", json=user_data)
    assert response.status_code == 201

    # Try to create second user with same email
    response = client.post("/v1/users/", json=user_data)
    assert response.status_code == 400

    error_data = response.json()
    assert error_data["error"] == "business_error"
    assert "correlation_id" in error_data
    assert "email" in str(error_data["details"]).lower()
    assert "X-Correlation-ID" in response.headers


def test_create_user_without_age():
    """Should create a user without age and set age to None."""
    user_data = {"name": "Jane Doe", "email": "jane@example.com"}
    response = client.post("/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"
    assert data["age"] is None


def test_create_user_with_whitespace():
    """Should strip whitespace from input fields when creating a user."""
    user_data = {"name": "  John Doe  ", "email": "john@example.com"}
    response = client.post("/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "John Doe"  # Whitespace should be stripped


def test_create_user_validation_errors():
    """Should return validation errors for invalid user creation data."""
    # Empty name
    response = client.post("/v1/users/", json={"name": "", "email": "test@example.com"})
    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data  # FastAPI default

    # Invalid age (negative)
    response = client.post(
        "/v1/users/", json={"name": "Test", "email": "test@example.com", "age": -1}
    )
    assert response.status_code == 422

    # Invalid age (too high)
    response = client.post(
        "/v1/users/", json={"name": "Test", "email": "test@example.com", "age": 200}
    )
    assert response.status_code == 422

    # Extra field (should be rejected)
    response = client.post(
        "/v1/users/",
        json={"name": "Test", "email": "test@example.com", "extra": "field"},
    )
    assert response.status_code == 422


def test_get_users_empty():
    """Should return an empty paginated response when no users exist."""
    response = client.get("/v1/users/")
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 100,
        "skip": 0,
    }
    assert "X-Correlation-ID" in response.headers


def test_get_users_with_pagination():
    """Should return paginated users with correct skip and limit."""
    # Create multiple users
    for i in range(5):
        user_data = {"name": f"User {i}", "email": f"user{i}@example.com"}
        client.post("/v1/users/", json=user_data)

    # Test pagination
    response = client.get("/v1/users/?skip=2&limit=2")
    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 2
    assert data["skip"] == 2
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "User 2"
    assert data["items"][1]["name"] == "User 3"


def test_get_user_by_id():
    """Should retrieve a user by their ID."""
    # Create a user first
    user_data = {"name": "Specific User", "email": "specific@example.com", "age": 25}
    create_response = client.post("/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    response = client.get(f"/v1/users/{user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Specific User"
    assert data["email"] == "specific@example.com"
    assert data["age"] == 25


def test_get_nonexistent_user():
    """Should return 404 when retrieving a non-existent user."""
    response = client.get("/v1/users/999")
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data  # FastAPI default


def test_update_user():
    """Should update an existing user's fields."""
    # Create a user first
    user_data = {"name": "Original Name", "email": "original@example.com", "age": 25}
    create_response = client.post("/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    # Update user
    update_data = {"name": "Updated Name", "age": 30}
    response = client.put(f"/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == "original@example.com"  # Unchanged
    assert data["age"] == 30


def test_update_user_email_conflict():
    """Should fail to update a user if the new email already exists."""
    # Create two users
    user1_data = {"name": "User 1", "email": "user1@example.com"}
    user2_data = {"name": "User 2", "email": "user2@example.com"}

    client.post("/v1/users/", json=user1_data)
    create_response = client.post("/v1/users/", json=user2_data)
    user2_id = create_response.json()["id"]

    # Try to update user2 with user1's email
    response = client.put(f"/v1/users/{user2_id}", json={"email": "user1@example.com"})
    assert response.status_code == 400

    error_data = response.json()
    assert error_data["error"] == "business_error"
    assert "email already exists" in error_data["message"]


def test_update_user_validation():
    """Should return validation errors for invalid user update data."""
    # Create a user first
    user_data = {"name": "Test User", "email": "test@example.com"}
    create_response = client.post("/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    # Try to update with invalid age
    response = client.put(f"/v1/users/{user_id}", json={"age": -1})
    assert response.status_code == 422

    # Try to update with extra field
    response = client.put(f"/v1/users/{user_id}", json={"extra": "field"})
    assert response.status_code == 422


def test_update_nonexistent_user():
    """Should return 404 when updating a non-existent user."""
    update_data = {"name": "New Name"}
    response = client.put("/v1/users/999", json=update_data)
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_delete_user():
    """Should delete a user and verify they no longer exist."""
    # Create a user first
    user_data = {"name": "To Delete", "email": "delete@example.com"}
    create_response = client.post("/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    # Delete user
    response = client.delete(f"/v1/users/{user_id}")
    assert response.status_code == 204
    assert "X-Correlation-ID" in response.headers

    # Verify user is deleted
    response = client.get(f"/v1/users/{user_id}")
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_delete_nonexistent_user():
    """Should return 404 when deleting a non-existent user."""
    response = client.delete("/v1/users/999")
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_create_user_invalid_email():
    """Should return a validation error for an invalid email address."""
    user_data = {"name": "Invalid Email User", "email": "not-an-email"}
    response = client.post("/v1/users/", json=user_data)
    assert response.status_code == 422  # Validation error
    error_data = response.json()
    assert "detail" in error_data
