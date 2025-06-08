from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserCreate(BaseModel):
    """Schema for creating a new user"""

    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_assignment=True,  # Validate on assignment
        extra="forbid",  # Forbid extra fields
    )


class UserUpdate(BaseModel):
    """Schema for updating a user"""

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
    """Schema for user in database"""

    id: int = Field(..., gt=0, description="User ID")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")
    created_at: datetime = Field(..., description="User creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for database models
        validate_assignment=True,
    )


class User(UserInDB):
    """Schema for user responses"""

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


class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
