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
from minimal_fastapi_app.projects.router import router as projects_router
from minimal_fastapi_app.users.models import Base as UserBase
from minimal_fastapi_app.users.router import router as users_router

# Configure logging before creating logger
configure_logging()
logger = get_logger(__name__)

settings = get_settings()

# Minimal tracing setup for context propagation (no exporters needed)
trace.set_tracer_provider(TracerProvider())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info(
        "Application starting up",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
    )

    # Create database tables
    engine = get_engine()
    async with engine.begin() as conn:
        from minimal_fastapi_app.projects.models import Base as ProjectBase

        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(ProjectBase.metadata.create_all)

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
app.add_middleware(RequestLoggingMiddleware)

# Instrument FastAPI for OpenTelemetry (for span/trace IDs in logs)
FastAPIInstrumentor().instrument_app(app)

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
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Validation failed",
            "details": exc.errors(),
        },
    )


# Include routers with proper prefix
app.include_router(users_router, tags=["users"])
app.include_router(projects_router, tags=["projects"])


@app.get("/", response_model=StatusResponse)
def read_root(request: Request):
    """Root endpoint with application status"""
    logger.info("Root endpoint accessed")
    return StatusResponse(
        message="Hello World",
        status="running",
        timestamp=datetime.now(),
        version=settings.app_version,
    )


@app.get("/health", response_model=HealthCheck)
def health_check(request: Request):
    """Health check endpoint"""
    logger.debug("Health check endpoint accessed")
    return HealthCheck(status="healthy")


@app.get("/info")
def app_info(request: Request):
    """Application information endpoint"""
    logger.info("App info endpoint accessed")
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
    }
