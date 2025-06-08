from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthCheck(BaseModel):
    """Health check response model"""

    status: Literal["healthy", "unhealthy"] = Field(
        ..., description="Application health status"
    )

    model_config = ConfigDict(json_schema_extra={"example": {"status": "healthy"}})


class StatusResponse(BaseModel):
    """Application status response model"""

    message: str = Field(..., description="Status message")
    status: Literal["running", "stopped", "maintenance"] = Field(
        ..., description="Application status"
    )
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(default="0.1.0", description="Application version")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Hello World",
                "status": "running",
                "timestamp": "2025-06-07T18:30:00.123456",
                "version": "0.1.0",
            }
        }
    )
