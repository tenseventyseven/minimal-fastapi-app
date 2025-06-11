"""
Service layer for user business logic and database operations.

Implements user CRUD operations with consistent logging, error handling,
and docstrings matching the projects feature.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.models import UserORM
from minimal_fastapi_app.users.schemas import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    """
    Service class for user-related business logic and database operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService with a database session.

        Args:
            db (AsyncSession): The database session.
        """
        self.db = db

    async def create_user(self, user_data: UserCreate) -> UserORM:
        """
        Create a new user.

        Args:
            user_data (UserCreate): The user creation payload.

        Returns:
            UserORM: The created user ORM object.

        Raises:
            BusinessException: If a user with the same email already exists or
                on DB error.
        """
        logger.info("Creating user", extra={"user_email": user_data.email})
        now = datetime.now()
        user = UserORM(
            **user_data.model_dump(),
            created_at=now,
            updated_at=now,
        )
        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError as exc:
            await self.db.rollback()
            logger.warning(
                "Duplicate email or DB error on user create",
                extra={"error": str(exc)},
            )
            raise BusinessException("A user with this email already exists.")
        logger.info("User created", extra={"user_id": user.user_id})
        return user

    async def get_users(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserORM], int]:
        """
        Retrieve a paginated list of users.

        Args:
            skip (int): Number of users to skip.
            limit (int): Number of users to return.

        Returns:
            tuple[list[UserORM], int]: List of user ORM objects and total count.
        """
        logger.info("Fetching users", extra={"skip": skip, "limit": limit})
        result = await self.db.execute(select(UserORM).offset(skip).limit(limit))
        users = list(result.scalars().all())
        total_result = await self.db.execute(select(func.count()).select_from(UserORM))
        total = total_result.scalar_one()
        logger.info("Fetched users", extra={"count": len(users)})
        return users, total

    async def get_user_by_id(self, user_id: str) -> UserORM:
        """
        Retrieve a user by user_id.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            UserORM: The user ORM object.

        Raises:
            BusinessException: If user is not found.
        """
        logger.info("Fetching user by id", extra={"user_id": user_id})
        result = await self.db.execute(
            select(UserORM).where(UserORM.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("User not found", extra={"user_id": user_id})
            raise BusinessException(f"User with user_id '{user_id}' not found")
        logger.info("User found", extra={"user_id": user_id})
        return user

    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserORM:
        """
        Update an existing user by user_id.

        Args:
            user_id (str): The unique user identifier.
            user_data (UserUpdate): The user update payload.

        Returns:
            UserORM: The updated user ORM object.

        Raises:
            BusinessException: If user is not found or on DB error.
        """
        logger.info("Updating user", extra={"user_id": user_id})
        user = await self.get_user_by_id(user_id)
        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        user.updated_at = datetime.now()
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError as exc:
            await self.db.rollback()
            logger.warning(
                "Duplicate email or DB error on user update",
                extra={"error": str(exc)},
            )
            raise BusinessException("A user with this email already exists.")
        logger.info("User updated", extra={"user_id": user_id})
        return user

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a user by user_id.

        Args:
            user_id (str): The unique user identifier.

        Raises:
            BusinessException: If user is not found.
        """
        logger.info("Deleting user", extra={"user_id": user_id})
        user = await self.get_user_by_id(user_id)
        await self.db.delete(user)
        await self.db.commit()
        logger.info("User deleted", extra={"user_id": user_id})
