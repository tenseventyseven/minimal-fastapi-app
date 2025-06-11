from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# 1. Base
class ProjectBase(BaseModel):
    """
    Base schema for project fields.

    Attributes:
        description (str, optional): Project description.
    """

    description: Optional[str] = Field(
        None, max_length=255, description="Project description"
    )
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


# 2. InDB
class ProjectInDB(ProjectBase):
    """
    Schema representing a project as stored in the database.
    Includes internal fields.

    Attributes:
        id (int): Database autoincrement ID.
        project_id (str): Unique project identifier.
        description (str, optional): Project description.
        created_at (datetime): Project creation timestamp.
        updated_at (datetime): Project last update timestamp.
    """

    id: int = Field(..., gt=0, description="Database autoincrement ID")
    project_id: str = Field(..., min_length=1, description="Unique project identifier")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )


# 3. API Response
class Project(ProjectInDB):
    """
    Schema for project returned in API responses.
    Inherits from ProjectInDB.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "project_id": "project-alpha",
                "description": "A test project",
                "created_at": "2025-06-07T18:30:00.123456",
                "updated_at": "2025-06-07T18:30:00.123456",
            }
        },
    )


# 4. Create
class ProjectCreate(ProjectBase):
    """
    Schema for creating a new project.

    All fields are required except description (optional).
    Attributes:
        project_id (str): Unique project identifier.
        description (str, optional): Project description.
    """

    project_id: str = Field(..., min_length=1, description="Unique project identifier")
    # description is inherited and remains optional
    # model_config is inherited from ProjectBase


# 5. Update
class ProjectUpdate(ProjectBase):
    """
    Schema for updating an existing project.

    All fields are optional.
    Attributes:
        project_id (str, optional): Unique project identifier.
        description (str, optional): Project description.
    """

    project_id: Optional[str] = Field(
        None, min_length=1, description="Unique project identifier"
    )
    # description is inherited and remains optional
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore",  # Allow PATCH to ignore extra fields for partial updates
    )
