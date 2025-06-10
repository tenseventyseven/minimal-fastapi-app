from datetime import datetime

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from minimal_fastapi_app.core.db import get_db_session
from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.models import UserORM
from minimal_fastapi_app.users.schemas import UserCreate, UserInDB, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service layer for user operations using SQLAlchemy async ORM."""

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create a new user in the database.
        Checks for duplicate email before creation.
        Raises BusinessException if email already exists.
        """
        logger.debug(
            "Attempting to create user",
            user_data=user_data.model_dump(),
        )
        # Use self.db instead of creating a new session
        existing = await self.db.execute(
            select(UserORM).where(UserORM.email == str(user_data.email))
        )
        if existing.scalar_one_or_none():
            raise BusinessException(
                message="A user with this email already exists",
                details=[
                    {
                        "field": "email",
                        "message": "Email address is already in use",
                        "code": "email_exists",
                    }
                ],
            )
        user = UserORM(
            given_name=user_data.given_name,
            family_name=user_data.family_name,
            email=str(user_data.email),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(
                "User created successfully",
                user_id=user.id,
            )
        except IntegrityError:
            await self.db.rollback()
            raise
        return UserInDB.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> UserInDB:
        """
        Retrieve a user by their unique ID.
        Raises BusinessException if user is not found.
        """
        logger.debug("Fetching user by ID", user_id=user_id)
        result = await self.db.execute(select(UserORM).where(UserORM.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.error(
                "User not found",
                user_id=user_id,
            )
            raise BusinessException(
                message=f"User with id '{user_id}' not found",
                details=[],
            )
        logger.info("User fetched successfully", user_id=user.id)
        return UserInDB.model_validate(user)

    async def get_users(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserInDB], int]:
        """
        Retrieve a paginated list of users and the total count.
        Useful for API pagination endpoints.
        """
        logger.debug(
            "Fetching users with pagination",
            skip=skip,
            limit=limit,
        )
        total = await self.db.scalar(select(func.count()).select_from(UserORM))
        result = await self.db.execute(select(UserORM).offset(skip).limit(limit))
        users = result.scalars().all()
        logger.info("Users fetched", count=len(users))
        return [UserInDB.model_validate(u) for u in users], int(total or 0)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserInDB:
        """
        Update an existing user's information by ID.
        Raises BusinessException if user not found or email is duplicate.
        """
        logger.debug(
            "Attempting to update user",
            user_id=user_id,
            user_data=user_data.model_dump(exclude_unset=True),
        )
        result = await self.db.execute(select(UserORM).where(UserORM.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.error(
                "User not found for update",
                user_id=user_id,
            )
            raise BusinessException(
                message=f"User with id '{user_id}' not found",
                details=[],
            )
        update_data = user_data.model_dump(exclude_unset=True)
        # Check for duplicate email (excluding self)
        if "email" in update_data:
            existing = await self.db.execute(
                select(UserORM).where(
                    (UserORM.email == update_data["email"]) & (UserORM.id != user_id)
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(
                    "Failed to update user due to duplicate email",
                    email=update_data["email"],
                )
                raise BusinessException(
                    message="A user with this email already exists",
                    details=[
                        {
                            "field": "email",
                            "message": "Email address is already in use",
                            "code": "email_exists",
                        }
                    ],
                )
        if user_data.given_name is not None:
            user.given_name = user_data.given_name
        if user_data.family_name is not None:
            user.family_name = user_data.family_name
        if user_data.email is not None:
            user.email = str(user_data.email)
        user.updated_at = datetime.now()
        try:
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(
                "User updated successfully",
                user_id=user.id,
            )
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Failed to update user due to duplicate email",
                email=update_data.get("email"),
            )
            raise BusinessException(
                message="A user with this email already exists",
                details=[
                    {
                        "field": "email",
                        "message": "Email address is already in use",
                        "code": "email_exists",
                    }
                ],
            )
        return UserInDB.model_validate(user)

    async def delete_user(self, user_id: int) -> None:
        """
        Delete a user by their unique ID.
        Raises BusinessException if user not found.
        """
        logger.debug("Attempting to delete user", user_id=user_id)
        result = await self.db.execute(select(UserORM).where(UserORM.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.error(
                "User not found for deletion",
                user_id=user_id,
            )
            raise BusinessException(
                message=f"User with id '{user_id}' not found",
                details=[],
            )
        await self.db.delete(user)
        await self.db.commit()
        logger.info("User deleted successfully", user_id=user_id)
