from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(
        None, max_length=255, description="Project description"
    )
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class ProjectInDB(BaseModel):
    id: int = Field(..., gt=0, description="Project ID")
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(
        None, max_length=255, description="Project description"
    )
    created_at: datetime = Field(..., description="Project creation timestamp")
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )


class Project(ProjectInDB):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Project Alpha",
                "description": "A sample project",
                "created_at": "2025-06-08T12:00:00.000000",
            }
        },
    )
