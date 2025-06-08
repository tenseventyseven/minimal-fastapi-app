from fastapi import Request, status
from fastapi.responses import JSONResponse


class BusinessException(Exception):
    def __init__(self, message: str, details: list | None = None):
        if details is None:
            details = []
        self.message = message
        self.details = details


def business_exception_handler(request: Request, exc: BusinessException):
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "business_error",
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id,
        },
        headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
    )


def enrich_log_fields(base: dict, request: Request, user_id=None):
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)
    # user_id can be passed explicitly or None
    fields = dict(base)
    fields["correlation_id"] = correlation_id
    fields["request_id"] = request_id
    if user_id is not None:
        fields["user_id"] = user_id
    return fields
