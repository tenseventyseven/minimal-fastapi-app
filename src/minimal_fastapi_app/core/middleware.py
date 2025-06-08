import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from minimal_fastapi_app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests with correlation IDs and timing"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            correlation_id=correlation_id,
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            correlation_id=correlation_id,
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
