import json
import os
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Supports robust parsing and validation for all fields, including
    ALLOWED_HOSTS as a list.
    """

    # Application settings
    app_name: str = Field(default="Minimal FastAPI App", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment name"
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        min_length=32,
        description="Secret key for security (minimum 32 characters)",
    )
    allowed_hosts: list[str] = Field(
        default=["*"],
        description="CORS allowed hosts (as a list or comma-separated string)",
    )

    # Database settings (for future use)
    database_url: str = Field(
        default=("postgresql+asyncpg://postgres:postgres@db:5432/postgres"),
        description="Database connection URL",
    )

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    json_logs: bool = Field(
        default=False, description="Enable JSON logging (useful for production)"
    )

    # External API settings (examples)
    external_api_key: str = Field(default="", description="External API key")
    external_api_url: str = Field(
        default="https://api.example.com", description="External API base URL"
    )

    # Feature flags
    enable_cors: bool = Field(default=True, description="Enable CORS middleware")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Pydantic v2 best practices
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True,  # Use enum values in serialization
        frozen=False,  # Allow mutation (can be True for immutable settings)
    )

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> list[str]:
        """Parse ALLOWED_HOSTS from environment as a list or comma-separated string."""
        if isinstance(v, str):
            v = v.strip()
            # Try JSON list first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                # Fallback: comma-separated
                return [host.strip() for host in v.split(",") if host.strip()]
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)] if v else []

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v, info):
        env = os.getenv("ENVIRONMENT", info.data.get("environment", "development"))
        if env == "production" and v == "your-secret-key-change-this-in-production":
            raise ValueError("SECRET_KEY must be set to a secure value in production.")
        if env == "production" and (not v or len(v) < 32):
            raise ValueError("SECRET_KEY must be at least 32 characters in production.")
        return v


def get_settings() -> Settings:
    """Return a Settings instance, always using current env vars."""
    return Settings()
