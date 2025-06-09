from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Pydantic schema for creating a new user.
    All fields required except age (optional).
    """

    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class UserUpdate(BaseModel):
    """
    Pydantic schema for updating an existing user.
    All fields optional.
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User's full name"
    )
    email: Optional[EmailStr] = Field(None, description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
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

    id: int = Field(..., gt=0, description="User ID")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
    created_at: datetime = Field(..., description="User creation timestamp")
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
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "created_at": "2025-06-07T18:30:00.123456",
            }
        },
    )
