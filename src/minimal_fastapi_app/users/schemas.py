from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Pydantic schema for creating a new user.
    All fields required.
    """

    user_id: str = Field(..., description="User's unique user_id")
    given_name: str = Field(
        ..., min_length=1, max_length=100, description="User's given name"
    )
    family_name: str = Field(
        ..., min_length=1, max_length=100, description="User's family name"
    )
    email: EmailStr = Field(..., description="User's email address")
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class UserUpdate(BaseModel):
    """
    Pydantic schema for updating an existing user.
    All fields optional, but user_id is not allowed.
    """

    given_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User's given name"
    )
    family_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User's family name"
    )
    email: Optional[EmailStr] = Field(None, description="User's email address")
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class UserInDB(BaseModel):
    """
    Pydantic schema representing a user as stored in the database.
    Includes internal fields.
    """

    id: int = Field(..., gt=0, description="Database autoincrement ID")
    user_id: str = Field(..., description="User's unique user_id")
    given_name: str = Field(
        ..., min_length=1, max_length=100, description="User's given name"
    )
    family_name: str = Field(
        ..., min_length=1, max_length=100, description="User's family name"
    )
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )


class User(UserInDB):
    """
    Pydantic schema for user returned in API responses.
    Inherits from UserInDB.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": "abc123",
                "given_name": "John",
                "family_name": "Doe",
                "email": "john@example.com",
                "created_at": "2025-06-07T18:30:00.123456",
                "updated_at": "2025-06-07T18:30:00.123456",
            }
        },
    )
