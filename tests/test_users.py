import uuid

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    """Should create a user and return correct fields."""
    unique_email = f"john-{uuid.uuid4()}@example.com"
    user_data = {
        "name": "John Doe",
        "email": unique_email,
        "age": 30,
    }
    response = await client.post("/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == unique_email
    assert data["age"] == 30
    assert isinstance(data["id"], int)
    assert data["id"] > 0
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_duplicate_email(app) -> None:
    """Should not allow duplicate emails."""
    unique_email = f"dup-{uuid.uuid4()}@example.com"
    user_data = {
        "name": "John Doe",
        "email": unique_email,
        "age": 30,
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create first user
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 201

        # Try to create second user with same email
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 400

        error_data = response.json()
        assert error_data["error"] == "business_error"
        assert "trace_id" in error_data
        assert "email" in str(error_data["details"]).lower()


@pytest.mark.asyncio
async def test_create_user_without_age(app) -> None:
    """Should create a user without age and set age to None."""
    user_data = {"name": "Jane Doe", "email": "jane@example.com"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["email"] == "jane@example.com"
        assert data["age"] is None


@pytest.mark.asyncio
async def test_create_user_with_whitespace(app) -> None:
    """Should trim whitespace from user name."""
    unique_email = f"whitespace-{uuid.uuid4()}@example.com"
    user_data = {"name": "  John Doe  ", "email": unique_email}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "John Doe"  # Whitespace should be stripped
        assert data["email"] == unique_email


@pytest.mark.asyncio
async def test_create_user_validation_errors(app) -> None:
    """Should return validation errors for invalid user creation data."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Empty name
        response = await ac.post(
            "/v1/users/", json={"name": "", "email": "test@example.com"}
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data  # FastAPI default

        # Invalid age (negative)
        response = await ac.post(
            "/v1/users/", json={"name": "Test", "email": "test@example.com", "age": -1}
        )
        assert response.status_code == 422

        # Invalid age (too high)
        response = await ac.post(
            "/v1/users/", json={"name": "Test", "email": "test@example.com", "age": 200}
        )
        assert response.status_code == 422

        # Extra field (should be rejected)
        response = await ac.post(
            "/v1/users/",
            json={"name": "Test", "email": "test@example.com", "extra": "field"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_users_empty(app) -> None:
    """Should return a paginated response (may not be empty if other tests ran)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "skip" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_get_users_with_pagination(app) -> None:
    """Should return paginated users with correct skip/limit."""
    unique_prefix = str(uuid.uuid4())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create multiple users
        for i in range(5):
            user_data = {
                "name": f"User {unique_prefix}-{i}",
                "email": f"user{unique_prefix}-{i}@example.com",
            }
            await ac.post("/v1/users/", json=user_data)

        # Test pagination
        response = await ac.get("/v1/users/?skip=2&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 2
        assert data["skip"] == 2
        assert len(data["items"]) == 2
        # Check that at least 2 users with the unique prefix exist in all users
        all_users_response = await ac.get("/v1/users/")
        all_users = all_users_response.json()["items"]
        matching = [u for u in all_users if unique_prefix in u["name"]]
        assert len(matching) == 5


@pytest.mark.asyncio
async def test_get_user_by_id(app) -> None:
    """Should retrieve a user by their ID."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create a user first
        user_data = {
            "name": "Specific User",
            "email": "specific@example.com",
            "age": 25,
        }
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        response = await ac.get(f"/v1/users/{user_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Specific User"
        assert data["email"] == "specific@example.com"
        assert data["age"] == 25


@pytest.mark.asyncio
async def test_get_nonexistent_user(app) -> None:
    """Should return 404 when retrieving a non-existent user."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/users/999")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data  # FastAPI default


@pytest.mark.asyncio
async def test_update_user(app) -> None:
    """Should update an existing user's fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create a user first
        user_data = {
            "name": "Original Name",
            "email": "original@example.com",
            "age": 25,
        }
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        # Update user
        update_data = {"name": "Updated Name", "age": 30}
        response = await ac.put(f"/v1/users/{user_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "original@example.com"  # Unchanged
        assert data["age"] == 30


@pytest.mark.asyncio
async def test_update_user_email_conflict(app) -> None:
    """Should not allow updating user to duplicate email."""
    unique1 = str(uuid.uuid4())
    unique2 = str(uuid.uuid4())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create two users
        user1_data = {"name": "User 1", "email": f"user1-{unique1}@example.com"}
        user2_data = {"name": "User 2", "email": f"user2-{unique2}@example.com"}

        await ac.post("/v1/users/", json=user1_data)
        create_response = await ac.post("/v1/users/", json=user2_data)
        user2_id = create_response.json()["id"]

        # Try to update user2 with user1's email
        response = await ac.put(
            f"/v1/users/{user2_id}", json={"email": user1_data["email"]}
        )
        assert response.status_code == 400

        error_data = response.json()
        assert error_data["error"] == "business_error"
        assert "email already exists" in error_data["message"]


@pytest.mark.asyncio
async def test_update_user_validation(app) -> None:
    """Should return validation errors for invalid user update data."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create a user first
        user_data = {"name": "Test User", "email": "test@example.com"}
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        # Try to update with invalid age
        response = await ac.put(f"/v1/users/{user_id}", json={"age": -1})
        assert response.status_code == 422

        # Try to update with extra field
        response = await ac.put(f"/v1/users/{user_id}", json={"extra": "field"})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_nonexistent_user(app) -> None:
    """Should return 404 when updating a non-existent user."""
    update_data = {"name": "New Name"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.put("/v1/users/999", json=update_data)
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data


@pytest.mark.asyncio
async def test_delete_user(app) -> None:
    """Should delete a user and verify they no longer exist."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create a user first
        user_data = {"name": "To Delete", "email": "delete@example.com"}
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["id"]

        # Delete user
        response = await ac.delete(f"/v1/users/{user_id}")
        assert response.status_code == 204

        # Verify user is deleted
        response = await ac.get(f"/v1/users/{user_id}")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data


@pytest.mark.asyncio
async def test_delete_nonexistent_user(app) -> None:
    """Should return 404 when trying to delete a non-existent user."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.delete("/v1/users/9999")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()


@pytest.mark.asyncio
async def test_create_user_validation_error(app) -> None:
    """Should return 422 for invalid user creation data (missing name and email)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json={"age": 42})
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data


@pytest.mark.asyncio
async def test_create_user_invalid_email(app) -> None:
    """Should return a validation error for an invalid email address."""
    user_data = {"name": "Invalid Email User", "email": "not-an-email"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "detail" in error_data
