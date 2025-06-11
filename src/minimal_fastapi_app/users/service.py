from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.models import UserORM
from minimal_fastapi_app.users.schemas import UserCreate, UserInDB, UserUpdate

logger = get_logger(__name__)


class UserService:
    """
    Service class for user-related business logic and database operations.
    Handles user creation, retrieval, update, and deletion, as well as business rules.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService with a database session.

        Args:
            db (AsyncSession): The database session.
        """
        self.db = db

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create a new user and return a validated Pydantic schema.
        Checks for duplicate email before creation.

        Args:
            user_data (UserCreate): The user creation payload.

        Returns:
            UserInDB: The created user as a validated Pydantic schema.

        Raises:
            BusinessException: If a user with the same email already exists or
                on database error.
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
        return UserInDB.model_validate(user)

    async def get_users(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserInDB], int]:
        """
        Retrieve a paginated list of users as Pydantic schemas.

        Args:
            skip (int): Number of users to skip.
            limit (int): Number of users to return.

        Returns:
            tuple[list[UserInDB], int]: List of user schemas and total count.
        """
        logger.info("Fetching users", extra={"skip": skip, "limit": limit})
        result = await self.db.execute(select(UserORM).offset(skip).limit(limit))
        users = list(result.scalars().all())
        total_result = await self.db.execute(select(func.count()).select_from(UserORM))
        total = total_result.scalar_one()
        logger.info("Fetched users", extra={"count": len(users)})
        return [UserInDB.model_validate(u) for u in users], total

    async def get_user_by_id(self, user_id: str) -> UserInDB:
        """
        Retrieve a user by user_id and return as a Pydantic schema.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            UserInDB: The user as a validated Pydantic schema.

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
        return UserInDB.model_validate(user)

    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserInDB:
        """
        Update an existing user by user_id and return as a Pydantic schema.
        Only provided fields will be updated.

        Args:
            user_id (str): The unique user identifier.
            user_data (UserUpdate): The user update payload.

        Returns:
            UserInDB: The updated user as a validated Pydantic schema.

        Raises:
            BusinessException: If user is not found or on DB error.
        """
        logger.info("Updating user", extra={"user_id": user_id})
        # Fetch user for update
        result = await self.db.execute(
            select(UserORM).where(UserORM.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("User not found", extra={"user_id": user_id})
            raise BusinessException(f"User with user_id '{user_id}' not found")
        # Update only provided fields
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
        return UserInDB.model_validate(user)

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a user by user_id.

        Args:
            user_id (str): The unique user identifier.

        Raises:
            BusinessException: If user is not found.
        """
        logger.info("Deleting user", extra={"user_id": user_id})
        # Fetch user for deletion
        result = await self.db.execute(
            select(UserORM).where(UserORM.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("User not found", extra={"user_id": user_id})
            raise BusinessException(f"User with user_id '{user_id}' not found")
        await self.db.delete(user)
        await self.db.commit()
        logger.info("User deleted", extra={"user_id": user_id})
