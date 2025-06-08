from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from minimal_fastapi_app.core.exceptions import BusinessException, enrich_log_fields
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.models import User, UserCreate, UserUpdate
from minimal_fastapi_app.users.service import user_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1/users",
    tags=["users"],
)


class PaginatedUsersResponse(BaseModel):
    """Paginated response model for users list API."""

    items: list[User]
    total: int
    limit: int
    skip: int


@router.post(
    "/",
    response_model=User,
    status_code=201,
    tags=["users"],
    description="Create a new user.",
)
def create_user(user_data: UserCreate, request: Request) -> User:
    """Create a new user and return the created user object.

    Args:
        user_data (UserCreate): The user creation payload.
        request (Request): The incoming HTTP request.

    Returns:
        User: The created user object.
    """

    logger.info(
        "Create user endpoint called",
        **enrich_log_fields({"user_email": user_data.email}, request),
    )

    try:
        user = user_service.create_user(user_data)
    except BusinessException as exc:
        # Business logic error (e.g., duplicate email)
        raise exc

    logger.info(
        "User creation endpoint completed",
        **enrich_log_fields({"user_id": user.id}, request, user_id=user.id),
    )

    return User.model_validate(user)


@router.get(
    "/",
    response_model=PaginatedUsersResponse,
    tags=["users"],
    description="Get all users with pagination and return a paginated response object.",
)
def get_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of users to return"),
) -> PaginatedUsersResponse:
    """Get all users with pagination and return a paginated response object.

    Args:
        request (Request): The incoming HTTP request.
        skip (int): Number of users to skip.
        limit (int): Number of users to return.

    Returns:
        PaginatedUsersResponse: Paginated list of users.
    """
    logger.info(
        "Get users endpoint called",
        **enrich_log_fields({"skip": skip, "limit": limit}, request),
    )
    users = user_service.get_users(skip=skip, limit=limit)
    total = len(user_service.users)
    # Convert UserInDB to User for response
    user_responses = [User.model_validate(user) for user in users]
    logger.info(
        "Get users endpoint completed",
        **enrich_log_fields({"returned_count": len(users)}, request),
    )
    return PaginatedUsersResponse(
        items=user_responses,
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/{user_id}",
    response_model=User,
    tags=["users"],
    description="Get a specific user by ID.",
)
def get_user(user_id: int, request: Request) -> User:
    """Get a specific user by ID.

    Args:
        user_id (int): The user ID.
        request (Request): The incoming HTTP request.

    Returns:
        User: The user object if found.

    Raises:
        HTTPException: If user is not found.
    """
    logger.info(
        "Get user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
    try:
        user = user_service.get_user_by_id(user_id)
    except BusinessException as exc:
        # Not found error
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "Get user endpoint completed",
        **enrich_log_fields({"user_id": user.id}, request, user_id=user.id),
    )
    return User.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=User,
    tags=["users"],
    description="Update a user by ID.",
)
def update_user(user_id: int, user_data: UserUpdate, request: Request) -> User:
    """Update a user by ID.

    Args:
        user_id (int): The user ID.
        user_data (UserUpdate): The user update payload.
        request (Request): The incoming HTTP request.

    Returns:
        User: The updated user object.

    Raises:
        HTTPException: If user is not found or update fails.
    """
    logger.info(
        "Update user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
    try:
        user = user_service.update_user(user_id, user_data)
    except BusinessException as exc:
        if "not found" in exc.message.lower():
            raise HTTPException(status_code=404, detail=exc.message)
        raise exc
    logger.info(
        "Update user endpoint completed",
        **enrich_log_fields({"user_id": user.id}, request, user_id=user.id),
    )
    return User.model_validate(user)


@router.delete(
    "/{user_id}", status_code=204, tags=["users"], description="Delete a user by ID."
)
def delete_user(user_id: int, request: Request) -> None:
    """Delete a user by ID.

    Args:
        user_id (int): The user ID.
        request (Request): The incoming HTTP request.

    Raises:
        HTTPException: If user is not found.
    """
    logger.info(
        "Delete user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
    try:
        user_service.delete_user(user_id)
    except BusinessException as exc:
        # Not found error
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "Delete user endpoint completed",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
