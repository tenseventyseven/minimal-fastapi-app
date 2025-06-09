from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from minimal_fastapi_app.core.config import get_settings
from minimal_fastapi_app.core.db import get_engine
from minimal_fastapi_app.core.exceptions import (
    BusinessException,
    business_exception_handler,
)
from minimal_fastapi_app.core.logging import configure_logging, get_logger
from minimal_fastapi_app.core.middleware import RequestLoggingMiddleware
from minimal_fastapi_app.core.models import HealthCheck, StatusResponse
from minimal_fastapi_app.projects.models import Base as ProjectBase
from minimal_fastapi_app.projects.router import (
    projects_tags_metadata,
)
from minimal_fastapi_app.projects.router import (
    router as projects_router,
)
from minimal_fastapi_app.users.models import Base as UserBase
from minimal_fastapi_app.users.router import (
    router as users_router,
)
from minimal_fastapi_app.users.router import (
    users_tags_metadata,
)

# Configure logging before creating logger
configure_logging()
logger = get_logger(__name__)

# Load application settings from environment/config
settings = get_settings()

# Minimal tracing setup for context propagation (no exporters needed)
trace.set_tracer_provider(TracerProvider())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events: startup and shutdown."""
    logger.info(
        "Application starting up",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
    )

    # Create database tables on startup (for demo/dev only; use migrations in prod)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(ProjectBase.metadata.create_all)

    yield

    # Shutdown
    logger.info("Application shutting down", app_name=settings.app_name)


# Create FastAPI app instance with metadata and middleware
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A minimal FastAPI application following best practices structure",
    debug=settings.debug,
    lifespan=lifespan,
    openapi_tags=users_tags_metadata + projects_tags_metadata,
)
# Register request logging middleware for trace/log correlation
app.add_middleware(RequestLoggingMiddleware)

# Instrument FastAPI for OpenTelemetry (for span/trace IDs in logs)
FastAPIInstrumentor().instrument_app(app)

# Add CORS middleware if enabled (and not already present)
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register exception handlers before including routers to ensure all errors are caught
app.add_exception_handler(BusinessException, business_exception_handler)  # type: ignore


# Global exception handler for HTTPException
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    # Returns consistent error format for HTTP errors
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.status_code,
            "detail": exc.detail,
            "details": [],  # Always include details, empty for HTTPException
        },
    )


# Global exception handler for RequestValidationError
@app.exception_handler(FastAPIRequestValidationError)
def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    # Returns consistent error format for validation errors
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Validation failed",
            "details": exc.errors(),
        },
    )


# Include routers with proper prefix and tags
app.include_router(users_router)
app.include_router(projects_router)


@app.get("/", response_model=StatusResponse)
def read_root(request: Request):
    """Root endpoint with application status."""
    logger.info("Root endpoint accessed")
    return StatusResponse(
        message="Hello World",
        status="running",
        timestamp=datetime.now(),
        version=settings.app_version,
    )


@app.get("/health", response_model=HealthCheck)
def health_check(request: Request):
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    return HealthCheck(status="healthy")


@app.get("/info")
def app_info(request: Request):
    """Application information endpoint."""
    logger.info("App info endpoint accessed")
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
    }
