from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """
    Pydantic schema for creating a new project.
    All fields required except description (optional).
    """

    project_id: str = Field(..., min_length=1, description="Unique project identifier")
    description: Optional[str] = Field(
        None, max_length=255, description="Project description"
    )
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class ProjectInDB(BaseModel):
    """
    Pydantic schema representing a project as stored in the database.
    Includes internal fields.
    """

    id: int = Field(..., gt=0, description="Project DB ID")
    project_id: str = Field(..., min_length=1, description="Unique project identifier")
    description: Optional[str] = Field(
        None, max_length=255, description="Project description"
    )
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )


class Project(ProjectInDB):
    """
    Pydantic schema for project returned in API responses.
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


class ProjectUpdate(BaseModel):
    """
    Pydantic schema for updating an existing project.
    All fields optional.
    """

    project_id: Optional[str] = Field(
        None, min_length=1, description="Unique project identifier"
    )
    description: Optional[str] = Field(
        None, max_length=255, description="Project description"
    )
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )
