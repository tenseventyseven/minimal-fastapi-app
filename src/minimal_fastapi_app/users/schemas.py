"""
Schemas for user API endpoints.

Defines Pydantic models for user creation, update, and response,
with field-level descriptions and OpenAPI examples.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Base schema for user fields.

    Attributes:
        given_name (str): The user's given (first) name.
        family_name (str): The user's family (last) name.
        email (EmailStr): The user's email address.
    """

    given_name: Optional[str] = Field(
        None,
        description="The user's given (first) name.",
        examples=["Alice"],
    )
    family_name: Optional[str] = Field(
        None,
        description="The user's family (last) name.",
        examples=["Smith"],
    )
    email: Optional[EmailStr] = Field(
        None,
        description="The user's email address.",
        examples=["alice.smith@example.com"],
    )

    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "example": {
                "given_name": "Alice",
                "family_name": "Smith",
                "email": "alice.smith@example.com",
            }
        },
    }


class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    All fields are required.
    """

    user_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "The unique user identifier. Must be 1-64 characters, "
            "alphanumeric, dash or underscore."
        ),
        examples=["user-1234"],
    )
    given_name: str = Field(
        min_length=1,
        max_length=64,
        description="The user's given (first) name.",
        examples=["Alice"],
    )
    family_name: str = Field(
        min_length=1,
        max_length=64,
        description="The user's family (last) name.",
        examples=["Smith"],
    )
    email: EmailStr = Field(
        description="The user's email address.", examples=["alice.smith@example.com"]
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "user_id": "user-1234",
                "given_name": "Alice",
                "family_name": "Smith",
                "email": "alice.smith@example.com",
            }
        },
    }


class UserUpdate(UserBase):
    """
    Schema for updating an existing user.

    All fields are optional for PATCH, but required for PUT (enforced in router).
    """

    model_config = {
        **UserBase.model_config,
        "json_schema_extra": {
            "example": {
                "given_name": "Alice",
                "family_name": "Smith",
                "email": "alice.smith@example.com",
            }
        },
    }


class User(UserBase):
    """
    Schema for user response object.

    Attributes:
        user_id (str): The unique user identifier.
        created_at (datetime): The creation timestamp.
        updated_at (datetime): The last update timestamp.
    """

    user_id: str = Field(
        description="The unique user identifier.", examples=["user_1234"]
    )
    created_at: datetime = Field(
        description="The creation timestamp.",
        examples=["2025-06-11T12:00:00"],
    )
    updated_at: datetime = Field(
        description="The last update timestamp.",
        examples=["2025-06-11T12:00:00"],
    )

    model_config = {
        **UserBase.model_config,
        "json_schema_extra": {
            "example": {
                "user_id": "user_1234",
                "given_name": "Alice",
                "family_name": "Smith",
                "email": "alice.smith@example.com",
                "created_at": "2025-06-11T12:00:00",
                "updated_at": "2025-06-11T12:00:00",
            }
        },
    }
