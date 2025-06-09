import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            client=str(request.client.host) if request.client else None,
            user_agent=request.headers.get("user-agent"),
            # Add more headers or info as needed
        )
        # Optionally, read the body (be careful with large bodies or streaming)
        try:
            body = await request.body()
            structlog.contextvars.bind_contextvars(body=body.decode("utf-8"))
        except Exception:
            pass  # Don't let logging break the app

        response = await call_next(request)
        return response
