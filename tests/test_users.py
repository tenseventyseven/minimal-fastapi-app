import uuid

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    """Should create a user and return correct fields."""
    unique_email = f"john-{uuid.uuid4()}@example.com"
    user_data = {
        "user_id": f"john-{uuid.uuid4()}".replace("-", ""),
        "given_name": "John",
        "family_name": "Doe",
        "email": unique_email,
    }
    response = await client.post("/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["given_name"] == "John"
    assert data["family_name"] == "Doe"
    assert data["email"] == unique_email
    assert "user_id" in data
    assert data["user_id"]
    assert "created_at" in data
    assert "updated_at" in data  # TDD: updated_at must be present


@pytest.mark.asyncio
async def test_create_duplicate_email(app) -> None:
    """Should not allow duplicate emails."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        email = f"bob-{uuid.uuid4()}@example.com"
        data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "Bob",
            "family_name": "Smith",
            "email": email,
        }
        await ac.post("/v1/users/", json=data)
        resp = await ac.post("/v1/users/", json=data)
        assert resp.status_code == 400
        assert "already exists" in resp.text


@pytest.mark.asyncio
async def test_create_user_without_age(app) -> None:
    """Should create a user without age and set age to None."""
    user_data = {
        "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
        "given_name": "Jane",
        "family_name": "Doe",
        "email": "jane@example.com",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["given_name"] == "Jane"
        assert data["family_name"] == "Doe"
        assert data["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_create_user_with_whitespace(app) -> None:
    """Should trim whitespace from user name."""
    unique_email = f"whitespace-{uuid.uuid4()}@example.com"
    user_data = {
        "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
        "given_name": "  John  ",
        "family_name": "  Doe  ",
        "email": unique_email,
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["given_name"] == "John"  # Whitespace should be stripped
        assert data["family_name"] == "Doe"  # Whitespace should be stripped
        assert data["email"] == unique_email


@pytest.mark.asyncio
async def test_create_user_validation_errors(app) -> None:
    """Should return validation errors for invalid user creation data."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Empty name
        response = await ac.post(
            "/v1/users/",
            json={
                "given_name": "",
                "family_name": "",
                "email": "test@example.com",
            },
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data  # FastAPI default

        # Extra field (should be rejected)
        response = await ac.post(
            "/v1/users/",
            json={
                "given_name": "Test",
                "family_name": "User",
                "email": "test@example.com",
                "extra": "field",
            },
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
                "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
                "given_name": f"User{unique_prefix}-{i}",
                "family_name": f"Fam{unique_prefix}-{i}",
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
        matching = [u for u in all_users if unique_prefix in u["given_name"]]
        assert len(matching) == 5


@pytest.mark.asyncio
async def test_get_user_by_id(app) -> None:
    """Should retrieve a user by their ID."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create a user first
        user_data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "Specific",
            "family_name": "User",
            "email": "specific@example.com",
        }
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["user_id"]

        response = await ac.get(f"/v1/users/{user_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["given_name"] == "Specific"
        assert data["family_name"] == "User"
        assert data["email"] == "specific@example.com"


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
    """Should update an existing user's fields (PUT and PATCH)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "Charlie",
            "family_name": "Smith",
            "email": f"charlie-{uuid.uuid4()}@example.com",
        }
        resp = await ac.post("/v1/users/", json=data)
        user = resp.json()
        user_id = user["user_id"]
        # PATCH: partial update
        patch_update = {"given_name": "CharliePatched"}
        resp2 = await ac.patch(f"/v1/users/{user_id}", json=patch_update)
        assert resp2.status_code == 200
        updated = resp2.json()
        assert updated["given_name"] == "CharliePatched"
        # PUT: full update (all fields required)
        put_update = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "CharliePut",
            "family_name": "SmithPut",
            "email": f"charlie-put-{uuid.uuid4()}@example.com",
        }
        resp3 = await ac.put(f"/v1/users/{user_id}", json=put_update)
        assert resp3.status_code == 200
        updated2 = resp3.json()
        assert updated2["given_name"] == "CharliePut"
        assert updated2["family_name"] == "SmithPut"
        assert updated2["email"].startswith("charlie-put-")


@pytest.mark.asyncio
async def test_update_user_email_conflict(app) -> None:
    """Should not allow updating user to duplicate email."""
    unique1 = str(uuid.uuid4())
    unique2 = str(uuid.uuid4())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create two users
        user1_data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "User1",
            "family_name": "Fam1",
            "email": f"user1-{unique1}@example.com",
        }
        user2_data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "User2",
            "family_name": "Fam2",
            "email": f"user2-{unique2}@example.com",
        }

        await ac.post("/v1/users/", json=user1_data)
        create_response = await ac.post("/v1/users/", json=user2_data)
        user2_id = create_response.json()["user_id"]

        # Try to update user2 with user1's email
        # PUT requires all fields
        response = await ac.put(
            f"/v1/users/{user2_id}",
            json={
                "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
                "given_name": "User2",
                "family_name": "Fam2",
                "email": user1_data["email"],
            },
        )
        # Now expecting 400 for duplicate email (business logic error)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_user_validation(app) -> None:
    """Should return validation errors for invalid user update data."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create a user first
        user_data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "TestUser",
            "family_name": "FamUser",
            "email": "test@example.com",
        }
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["user_id"]

        # Try to update with extra field
        response = await ac.put(f"/v1/users/{user_id}", json={"extra": "field"})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_nonexistent_user(app) -> None:
    """Should return 404 when updating a non-existent user."""
    update_data = {
        "given_name": "NewGiven",
        "family_name": "NewFamily",
        "email": "new@example.com",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.put("/v1/users/nonexistent-user-id", json=update_data)
        # Now expecting 404 only if validation passes.
        # Otherwise 422 for missing required fields.
        # Since user_id does not exist but data is valid, expect 404
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
        user_data = {
            "user_id": f"user-{uuid.uuid4()}".replace("-", ""),
            "given_name": "To",
            "family_name": "Delete",
            "email": "delete@example.com",
        }
        create_response = await ac.post("/v1/users/", json=user_data)
        user_id = create_response.json()["user_id"]

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
        response = await ac.post("/v1/users/", json={})
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data


@pytest.mark.asyncio
async def test_create_user_invalid_email(app) -> None:
    """Should return a validation error for an invalid email address."""
    user_data = {"given_name": "Invalid Email User", "email": "not-an-email"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/users/", json=user_data)
        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "detail" in error_data
