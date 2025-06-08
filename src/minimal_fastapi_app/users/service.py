from datetime import datetime
from typing import List

from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.users.models import UserCreate, UserInDB, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service layer for user operations"""

    def __init__(self):
        self.users: List[UserInDB] = []
        self.user_counter = 1
        logger.info("UserService initialized")

    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user"""
        logger.info(
            "Creating user",
            user_email=user_data.email,
            user_name=user_data.name,
            has_age=user_data.age is not None,
        )

        # Business logic: Check if email already exists
        if any(user.email == str(user_data.email) for user in self.users):
            logger.warning(
                "User creation failed - email already exists",
                user_email=user_data.email,
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

        user = UserInDB(
            id=self.user_counter,
            name=user_data.name,
            email=str(user_data.email),
            age=user_data.age,
            created_at=datetime.now(),
        )

        self.users.append(user)
        self.user_counter += 1

        logger.info(
            "User created successfully",
            user_id=user.id,
            user_email=user.email,
            total_users=len(self.users),
        )

        return user

    def get_user_by_id(self, user_id: int) -> UserInDB:
        """Get a user by ID"""
        logger.debug("Looking up user by ID", user_id=user_id)

        user = next((user for user in self.users if user.id == user_id), None)

        if not user:
            logger.info("User not found", user_id=user_id, total_users=len(self.users))
            raise BusinessException(
                message=f"User with id '{user_id}' not found",
                details=[],
            )

        logger.debug("User found", user_id=user.id, user_email=user.email)
        return user

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """Get all users with pagination"""
        logger.debug(
            "Retrieving users with pagination",
            skip=skip,
            limit=limit,
            total_users=len(self.users),
        )

        users = self.users[skip : skip + limit]

        logger.info(
            "Users retrieved",
            returned_count=len(users),
            skip=skip,
            limit=limit,
            total_users=len(self.users),
        )

        return users

    def update_user(self, user_id: int, user_data: UserUpdate) -> UserInDB:
        """Update a user"""
        logger.info(
            "Updating user",
            user_id=user_id,
            update_fields=[
                field
                for field, value in user_data.model_dump(exclude_unset=True).items()
            ],
        )

        user = self.get_user_by_id(
            user_id
        )  # This will raise BusinessException if not found

        # Check for email conflicts if email is being updated
        update_data = user_data.model_dump(exclude_unset=True)
        if "email" in update_data:
            new_email = str(update_data["email"])
            if any(u.email == new_email and u.id != user_id for u in self.users):
                logger.warning(
                    "User update failed - email already exists",
                    user_id=user_id,
                    new_email=new_email,
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

        # Update only provided fields
        for field, value in update_data.items():
            setattr(user, field, value)

        logger.info(
            "User updated successfully",
            user_id=user.id,
            user_email=user.email,
            updated_fields=list(update_data.keys()),
        )

        return user

    def delete_user(self, user_id: int) -> None:
        """Delete a user"""
        logger.info("Deleting user", user_id=user_id)

        user = self.get_user_by_id(
            user_id
        )  # This will raise BusinessException if not found
        self.users.remove(user)

        logger.info(
            "User deleted successfully",
            user_id=user_id,
            user_email=user.email,
            remaining_users=len(self.users),
        )


# Global service instance
user_service = UserService()
