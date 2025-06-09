from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from minimal_fastapi_app.core.db import get_async_session
from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.models import UserORM
from minimal_fastapi_app.users.schemas import UserCreate, UserInDB, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service layer for user operations using SQLAlchemy async ORM"""

    def __init__(self):
        self.async_session_factory = get_async_session()

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        logger.debug(
            "Attempting to create user",
            user_data=user_data.model_dump(),
        )
        async with self.async_session_factory() as session:
            user = UserORM(
                name=user_data.name,
                email=str(user_data.email),
                age=user_data.age,
                created_at=datetime.now(),
            )
            session.add(user)
            try:
                await session.commit()
                await session.refresh(user)
                logger.info(
                    "User created successfully",
                    user_id=user.id,
                )
            except IntegrityError:
                await session.rollback()
                logger.warning(
                    "Failed to create user due to duplicate email",
                    email=user_data.email,
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

    async def get_user_by_id(self, user_id: int) -> UserInDB:
        logger.debug("Fetching user by ID", user_id=user_id)
        async with self.async_session_factory() as session:
            result = await session.execute(select(UserORM).where(UserORM.id == user_id))
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
        logger.debug(
            "Fetching users with pagination",
            skip=skip,
            limit=limit,
        )
        async with self.async_session_factory() as session:
            total_result = await session.execute(
                select(func.count()).select_from(UserORM)
            )
            total = total_result.scalar_one()
            result = await session.execute(select(UserORM).offset(skip).limit(limit))
            users = result.scalars().all()
            logger.info("Users fetched", count=len(users))
            return [UserInDB.model_validate(u) for u in users], total

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserInDB:
        logger.debug(
            "Attempting to update user",
            user_id=user_id,
            user_data=user_data.model_dump(exclude_unset=True),
        )
        async with self.async_session_factory() as session:
            result = await session.execute(select(UserORM).where(UserORM.id == user_id))
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
            for field, value in update_data.items():
                setattr(user, field, value)
            try:
                await session.commit()
                await session.refresh(user)
                logger.info(
                    "User updated successfully",
                    user_id=user.id,
                )
            except IntegrityError:
                await session.rollback()
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
        logger.debug("Attempting to delete user", user_id=user_id)
        async with self.async_session_factory() as session:
            result = await session.execute(select(UserORM).where(UserORM.id == user_id))
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
            await session.delete(user)
            await session.commit()
            logger.info("User deleted successfully", user_id=user_id)
