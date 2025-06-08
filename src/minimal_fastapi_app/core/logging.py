import logging
from typing import Any

import structlog

from minimal_fastapi_app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application"""

    # Determine if we should use JSON or console output
    use_json = settings.json_logs or settings.environment == "production"

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON or console renderer based on environment
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=structlog.dev.plain_traceback
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level),
        handlers=[logging.StreamHandler()],
    )


def get_logger(name: str) -> Any:
    """Get a structured logger instance"""
    return structlog.get_logger(name)
