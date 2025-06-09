import logging
from typing import Any

import structlog
from opentelemetry import trace

from minimal_fastapi_app.core.config import get_settings

# Silence all SQLAlchemy logs unless WARNING or above
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
# Silence aiosqlite and sqlite3 logs unless WARNING or above
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logging.getLogger("sqlite3").setLevel(logging.WARNING)
# Silence Uvicorn and FastAPI logs unless WARNING or above
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.WARNING)


def configure_logging() -> None:
    """
    Configure structlog for JSON logging and OpenTelemetry context extraction only.
    Sets up log level, format, and OpenTelemetry trace/span ID enrichment.
    """
    settings = get_settings()
    use_json = settings.json_logs or settings.environment == "production"

    # Set up structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # Add OpenTelemetry trace/span IDs to logs
        add_otel_trace_ids,
    ]
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up stdlib logging to go through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, settings.log_level),
    )


def add_otel_trace_ids(logger, method_name, event_dict):
    """
    Add OpenTelemetry trace_id and span_id to structlog event dict.
    If no active span, sets them to None.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    else:
        event_dict["trace_id"] = None
        event_dict["span_id"] = None
    return event_dict


def get_logger(name: str) -> Any:
    """Get a structlog logger instance."""
    return structlog.get_logger(name)
