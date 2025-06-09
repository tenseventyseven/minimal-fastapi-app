from fastapi import Request, status
from fastapi.responses import JSONResponse
from opentelemetry import trace


class BusinessException(Exception):
    def __init__(self, message: str, details: list | None = None):
        if details is None:
            details = []
        self.message = message
        self.details = details


def business_exception_handler(request: Request, exc: BusinessException):
    # Get OpenTelemetry trace ID
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    trace_id = format(ctx.trace_id, "032x") if ctx and ctx.is_valid else None
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "business_error",
            "message": exc.message,
            "details": exc.details,
            "trace_id": trace_id,
        },
        headers={"X-Trace-ID": trace_id} if trace_id else None,
    )


def enrich_log_fields(base: dict, request: Request, user_id=None):
    # Get OpenTelemetry trace ID
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    trace_id = format(ctx.trace_id, "032x") if ctx and ctx.is_valid else None
    fields = dict(base)
    fields["trace_id"] = trace_id
    if user_id is not None:
        fields["user_id"] = user_id
    return fields
