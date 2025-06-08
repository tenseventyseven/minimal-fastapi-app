from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from minimal_fastapi_app.core.config import settings
from minimal_fastapi_app.core.exceptions import (
    BusinessException,
    business_exception_handler,
)
from minimal_fastapi_app.core.logging import configure_logging, get_logger
from minimal_fastapi_app.core.middleware import RequestLoggingMiddleware
from minimal_fastapi_app.core.models import HealthCheck, StatusResponse
from minimal_fastapi_app.users.router import router as users_router

# Configure logging before creating logger
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(
        "Application starting up",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
    )

    yield

    # Shutdown
    logger.info("Application shutting down", app_name=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A minimal FastAPI application following best practices structure",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add middleware (order matters - first added = outermost)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware if enabled
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Register only the business exception handler (ignore type checker false positive)
app.add_exception_handler(BusinessException, business_exception_handler)  # type: ignore


# Global exception handler for HTTPException
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.status_code,
            "detail": exc.detail,
            "details": [],  # Always include details, empty for HTTPException
            "correlation_id": correlation_id,
        },
    )


# Global exception handler for RequestValidationError
@app.exception_handler(FastAPIRequestValidationError)
def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Validation failed",
            "details": exc.errors(),
            # Always include details, use errors for validation
            "correlation_id": correlation_id,
        },
    )


# Include routers with proper prefix
app.include_router(users_router, tags=["users"])


@app.get("/", response_model=StatusResponse)
def read_root(request: Request):
    """Root endpoint with application status"""
    correlation_id = getattr(request.state, "correlation_id", None)

    logger.info("Root endpoint accessed", correlation_id=correlation_id)

    return StatusResponse(
        message="Hello World",
        status="running",
        timestamp=datetime.now(),
        version=settings.app_version,
    )


@app.get("/health", response_model=HealthCheck)
def health_check(request: Request):
    """Health check endpoint"""
    correlation_id = getattr(request.state, "correlation_id", None)

    logger.debug("Health check endpoint accessed", correlation_id=correlation_id)

    return HealthCheck(status="healthy")


@app.get("/info")
def app_info(request: Request):
    """Application information endpoint"""
    correlation_id = getattr(request.state, "correlation_id", None)

    logger.info("App info endpoint accessed", correlation_id=correlation_id)

    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
    }
