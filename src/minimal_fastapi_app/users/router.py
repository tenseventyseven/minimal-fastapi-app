from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from minimal_fastapi_app.core.db import get_db_session
from minimal_fastapi_app.core.exceptions import BusinessException, enrich_log_fields
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.schemas import User, UserCreate, UserUpdate
from minimal_fastapi_app.users.service import UserService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1/users",
    tags=["users"],
    responses={
        404: {"description": "User not found."},
        400: {"description": "Validation or business logic error."},
    },
)


class PaginatedUsersResponse(BaseModel):
    """
    Paginated response model for users list API.

    Attributes:
        items (list[User]): List of user objects.
        total (int): Total number of users available.
        limit (int): Number of users returned in this page.
        skip (int): Number of users skipped (offset).
    """

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
    summary="Create User",
    operation_id="createUser",
    responses={
        201: {"description": "User created successfully."},
        400: {"description": "Duplicate email or validation error."},
    },
)
async def create_user(
    user_data: UserCreate, request: Request, db: AsyncSession = Depends(get_db_session)
) -> User:
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
    user_service = UserService(db)
    try:
        user = await user_service.create_user(user_data)
    except BusinessException as exc:
        raise HTTPException(status_code=400, detail=exc.message)

    logger.info(
        "User creation endpoint completed",
        **enrich_log_fields({"user_id": user.user_id}, request, user_id=user.user_id),
    )

    return User.model_validate(user)


@router.get(
    "/",
    response_model=PaginatedUsersResponse,
    tags=["users"],
    description="Get all users with pagination.",
    summary="List Users",
    operation_id="listUsers",
    responses={
        200: {"description": "Paginated list of users."},
    },
)
async def get_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of users to return"),
    db: AsyncSession = Depends(get_db_session),
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
    user_service = UserService(db)
    users, total = await user_service.get_users(skip=skip, limit=limit)
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
    description="Get a specific user by user_id.",
    summary="Get User",
    operation_id="getUser",
    responses={
        200: {"description": "User found."},
        404: {"description": "User not found."},
    },
)
async def get_user(
    user_id: str, request: Request, db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get a specific user by user_id (string).

    Args:
        user_id (str): The user_id.
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
    user_service = UserService(db)
    try:
        user = await user_service.get_user_by_id(user_id)
    except BusinessException as exc:
        # Not found error
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "Get user endpoint completed",
        **enrich_log_fields({"user_id": user.user_id}, request, user_id=user.user_id),
    )
    return User.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=User,
    tags=["users"],
    description=(
        "Update a user by user_id. All fields must be provided. "
        "Missing fields will be set to null or default."
    ),
    summary="Update User",
    operation_id="updateUser",
    responses={
        200: {"description": "User updated successfully."},
        400: {"description": "Duplicate email or validation error."},
        404: {"description": "User not found."},
    },
)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Replace all fields of a user by user_id.

    Args:
        user_id (str): The unique user identifier from the path.
        user_data (UserUpdate): The new user data (all fields required).
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Returns:
        User: The updated user object.

    Raises:
        HTTPException: 422 if any required field is missing,
        404 if user not found,
        400 for business/validation errors.
    """
    logger.info(
        "Update user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
    # Ensure all required fields are present for a full update (PUT)
    missing_fields = [
        field
        for field in ["given_name", "family_name", "email"]
        if getattr(user_data, field) is None
    ]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "message": (
                    f"PUT requires all fields: missing {', '.join(missing_fields)}"
                ),
                "fields": missing_fields,
            },
        )
    user_service = UserService(db)
    try:
        user = await user_service.update_user(user_id, user_data)
    except BusinessException as exc:
        if "not found" in exc.message.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": exc.message,
                    "user_id": user_id,
                },
            )
        raise HTTPException(
            status_code=400, detail={"error": "business_error", "message": exc.message}
        )
    logger.info(
        "Update user endpoint completed",
        **enrich_log_fields({"user_id": user.user_id}, request, user_id=user.user_id),
    )
    return User.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=User,
    tags=["users"],
    description="Partially update a user by user_id.",
    summary="Patch User",
    operation_id="patchUser",
    responses={
        200: {"description": "User updated successfully."},
        400: {"description": "Duplicate email or validation error."},
        404: {"description": "User not found."},
    },
)
async def patch_user(
    user_id: str,
    user_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Partially update a user by user_id.

    Args:
        user_id (str): The unique user identifier from the path.
        user_data (UserUpdate): The user update payload (partial; only provided
            fields will be updated).
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Returns:
        User: The updated user object.

    Raises:
        HTTPException: 404 if user not found, 400 for business/validation errors.
    """
    logger.info(
        "Patch user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
    user_service = UserService(db)
    try:
        user = await user_service.update_user(user_id, user_data)
    except BusinessException as exc:
        if "not found" in exc.message.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": exc.message,
                    "user_id": user_id,
                },
            )
        raise HTTPException(
            status_code=400, detail={"error": "business_error", "message": exc.message}
        )
    logger.info(
        "Patch user endpoint completed",
        **enrich_log_fields({"user_id": user.user_id}, request, user_id=user.user_id),
    )
    return User.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=204,
    tags=["users"],
    description="Delete a user by user_id.",
    summary="Delete User",
    operation_id="deleteUser",
    responses={
        204: {"description": "User deleted successfully."},
        404: {"description": "User not found."},
    },
)
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a user by user_id.

    Args:
        user_id (str): The unique user identifier from the path.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Raises:
        HTTPException: 404 if user not found.
    """
    logger.info(
        "Delete user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
    user_service = UserService(db)
    try:
        await user_service.delete_user(user_id)
    except BusinessException:
        # Return plain string for detail to match test expectations
        raise HTTPException(
            status_code=404, detail=f"User with user_id '{user_id}' not found"
        )
    logger.info(
        "Delete user endpoint completed",
        **enrich_log_fields({"user_id": user_id}, request, user_id=user_id),
    )
