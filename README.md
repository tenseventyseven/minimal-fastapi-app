# Minimal FastAPI App

A production-ready FastAPI application using modern Python tooling with uv, hatchling, and containerized deployment with nginx.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Pydantic** - Data validation and settings management using Python type annotations
- **pydantic-settings** - Settings management from environment variables
- **structlog** - Structured logging with correlation IDs and JSON output
- **uv** - Ultra-fast Python package manager and project management
- **Hatchling** - Modern Python build backend
- **Src layout** - Standard Python package structure
- **Docker/Podman** - Containerized deployment
- **nginx** - Production reverse proxy
- **pytest** - Comprehensive testing setup
- **ruff** - Ultra-fast Python linter and formatter

## Project Structure

```
minimal-fastapi-app/
├── src/
│   └── minimal_fastapi_app/
│       ├── __init__.py
│       ├── main.py              # FastAPI application factory
│       ├── core/                # Core functionality
│       │   ├── __init__.py
│       │   ├── models.py        # Shared models (health, status)
│       │   ├── config.py        # Settings and configuration
│       │   ├── logging.py       # Structured logging setup
│       │   ├── middleware.py    # Request/response middleware
│       │   └── exceptions.py    # Custom exception handlers
│       └── users/               # User feature module
│           ├── __init__.py
│           ├── models.py        # User-specific Pydantic models
│           ├── router.py        # User routes/endpoints
│           └── service.py       # User business logic
├── tests/
│   ├── __init__.py
│   ├── test_main.py             # Main application tests
│   ├── test_users.py            # User feature tests
│   └── test_config.py           # Configuration tests
├── .env.example                 # Example environment variables
├── .env.development             # Development environment config
├── .env.production              # Production environment config
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lock file
├── Dockerfile                   # Container definition
├── compose.yaml                 # Multi-container orchestration
├── nginx.conf                   # nginx configuration
├── .dockerignore                # Files to exclude from Docker builds
├── .gitignore                   # Files to exclude from Git
└── README.md
```

## Prerequisites

- **Python 3.13+**
- **uv** - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker/Podman** - For containerized deployment

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd minimal-fastapi-app

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your specific values
```

### Development with different environments

```bash
# Development mode
cp .env.development .env
uv run uvicorn minimal_fastapi_app.main:app --reload

# Production-like testing
cp .env.production .env
uv run uvicorn minimal_fastapi_app.main:app --host 0.0.0.0 --port 8000

# Override settings with environment variables
DEBUG=true LOG_LEVEL=DEBUG uv run uvicorn minimal_fastapi_app.main:app --reload
```

### 3. Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=minimal_fastapi_app

# Run specific test file
uv run pytest tests/test_main.py -v
```

### 4. Code Quality

```bash
# Add ruff for linting and formatting
uv add --dev ruff

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix auto-fixable lint issues
uv run ruff check --fix .
```

### 5. Production Deployment

```bash
# Build and run with Docker/Podman
podman-compose up -d --build

# Or with Docker Compose
docker-compose up -d --build

# Application will be available at http://localhost:8000
```

## API Endpoints

| Method | Endpoint      | Description                                            |
| ------ | ------------- | ------------------------------------------------------ |
| GET    | `/`           | Root endpoint - returns welcome message with timestamp |
| GET    | `/health`     | Health check endpoint                                  |
| GET    | `/info`       | Application information and configuration              |
| POST   | `/users/`     | Create a new user                                      |
| GET    | `/users/`     | Get all users (with pagination)                        |
| GET    | `/users/{id}` | Get specific user by ID                                |
| PUT    | `/users/{id}` | Update specific user by ID                             |
| DELETE | `/users/{id}` | Delete specific user by ID                             |

### Example Responses

**GET /**

```json
{
  "message": "Hello World",
  "status": "running",
  "timestamp": "2025-06-07T18:30:00.123456"
}
```

**GET /health**

```json
{
  "status": "healthy"
}
```

**GET /info**

```json
{
  "app_name": "Minimal FastAPI App",
  "version": "0.1.0",
  "environment": "development",
  "debug": false,
  "metrics_enabled": false
}
```

**POST /users/**

```bash
# Request
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  }'

# Response
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30,
  "created_at": "2025-06-07T18:30:00.123456"
}
```

**GET /users/ (with pagination)**

```bash
# Get first 10 users
curl "http://localhost:8000/users/?skip=0&limit=10"

# Get next 10 users
curl "http://localhost:8000/users/?skip=10&limit=10"
```

**PUT /users/1**

```bash
# Update user
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "age": 35}'

# Response
{
  "id": 1,
  "name": "Updated Name",
  "email": "john@example.com",
  "age": 35,
  "created_at": "2025-06-07T18:30:00.123456"
}
```

**DELETE /users/1**

```bash
# Delete user
curl -X DELETE "http://localhost:8000/users/1"
# Returns 204 No Content
```

**GET /users/1**

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30,
  "created_at": "2025-06-07T18:30:00.123456"
}
```

## Development Commands

### Package Management

```bash
# Add new dependency
uv add requests

# Add development dependency
uv add --dev ruff

# Add settings management
uv add pydantic-settings

# Add structured logging
uv add structlog

# Remove dependency
uv remove requests

# Update dependencies
uv sync
```

### Building

```bash
# Build Python package
uv build

# Clean build artifacts
rm -rf dist/ *.egg-info
```

### Testing

```bash
# All tests
uv run pytest

# With coverage report
uv run pytest --cov=minimal_fastapi_app --cov-report=html

# Specific test pattern
uv run pytest -k "test_health"

# Watch mode (requires pytest-watch)
uv add --dev pytest-watch
uv run ptw
```

## Container Management

### Development

```bash
# Build image
podman build -t minimal-fastapi-app .

# Run container
podman run -p 8000:8001 minimal-fastapi-app
```

### Production with nginx

```bash
# Start services
podman-compose up -d

# View logs
podman-compose logs -f fastapi
podman-compose logs -f nginx

# Stop services
podman-compose down

# Rebuild and restart
podman-compose up -d --build
```

### Verify Deployment

```bash
# Check containers are running
podman-compose ps

# Test the application
curl http://localhost:8000/
curl http://localhost:8000/health

# Check logs if needed
podman-compose logs fastapi
podman-compose logs nginx
```

## Observability & Monitoring

### Structured Logging

The application uses [structlog](https://www.structlog.org/) for structured logging with the following features:

**Development Mode:**

```bash
# Colored console output with readable format
2025-06-07T18:30:15.123456Z [info] Request started [minimal_fastapi_app.core.middleware] method=POST url=http://localhost:8000/users/ correlation_id=abc-123-def
```

**Production Mode (JSON):**

```json
{
  "timestamp": "2025-06-07T18:30:15.123456Z",
  "level": "info",
  "logger": "minimal_fastapi_app.core.middleware",
  "message": "Request started",
  "method": "POST",
  "url": "http://localhost:8000/users/",
  "correlation_id": "abc-123-def",
  "client_ip": "127.0.0.1"
}
```

**Configuration:**

```bash
# Enable JSON logging
JSON_LOGS=true

# Set log level
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Request Correlation

Every request gets a unique correlation ID that tracks through:

- Request/response logs
- Business logic logs
- Error responses
- Response headers (`X-Correlation-ID`)

**Example Usage in Code:**

```python
from ..core.logging import get_logger

logger = get_logger(__name__)

def create_user(user_data):
    logger.info(
        "Creating user",
        user_email=user_data.email,
        user_name=user_data.name
    )
    # Correlation ID automatically included
```

### Error Handling (Modern FastAPI Best Practice)

This project uses a simple, modern approach to error handling:

- **Validation errors** and **HTTP errors** are handled with a single, consistent JSON response format.
- **Business logic errors** (like duplicate email) use a custom `BusinessException` for clarity and testability.
- All error responses include a `correlation_id` for traceability.

**Example error responses:**

Business logic error:

```json
{
  "error": "business_error",
  "message": "A user with this email already exists",
  "detail": "A user with this email already exists",
  "details": [
    {
      "field": "email",
      "message": "Email address is already in use",
      "code": "email_exists"
    }
  ],
  "correlation_id": "abc-123-def"
}
```

Validation error:

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "detail": "Request validation failed",
  "details": [
    {
      "loc": ["body", "age"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ],
  "correlation_id": "abc-123-def"
}
```

404 not found error:

```json
{
  "error": "not_found",
  "message": "User with id '999' not found",
  "detail": "User with id '999' not found",
  "details": [],
  "correlation_id": "abc-123-def"
}
```

**How it works:**

- See `src/minimal_fastapi_app/core/exceptions.py` for the simple, DRY implementation.
- See `src/minimal_fastapi_app/main.py` for how exception handlers are registered.
- Raise `BusinessException` in your service layer for business logic errors.
- Raise `HTTPException(status_code=404, detail=...)` for not found.

This approach is robust, easy to maintain, and matches modern FastAPI best practices.

### Security Headers

Automatically added security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (HTTPS only)

### Monitoring Endpoints

| Endpoint  | Purpose                                   |
| --------- | ----------------------------------------- |
| `/health` | Basic health check                        |
| `/info`   | Application information and configuration |
| `/docs`   | Interactive API documentation             |

## Troubleshooting

### Log Analysis

**Find all requests for a specific user:**

```bash
# Using correlation ID
grep "abc-123-def" app.log

# Using structured search (if using JSON logs)
jq 'select(.correlation_id == "abc-123-def")' app.log
```

**Find all errors:**

```bash
# Text logs
grep "ERROR" app.log

# JSON logs
jq 'select(.level == "error")' app.log
```

**Monitor request performance:**

```bash
# JSON logs - requests taking longer than 1000ms
jq 'select(.message == "Request completed" and .duration_ms > 1000)' app.log
```

### Environment Variables

The application uses pydantic-settings for configuration management. Settings can be configured via environment variables or `.env` files.

#### Setup Environment Files

```bash
# Copy example file and customize
cp .env.example .env

# Or use environment-specific files
cp .env.development .env  # For development
cp .env.production .env   # For production
```

#### Available Settings

| Variable           | Default                 | Description                                  |
| ------------------ | ----------------------- | -------------------------------------------- |
| `APP_NAME`         | "Minimal FastAPI App"   | Application name                             |
| `APP_VERSION`      | "0.1.0"                 | Application version                          |
| `DEBUG`            | false                   | Enable debug mode                            |
| `ENVIRONMENT`      | development             | Environment (development/staging/production) |
| `HOST`             | 0.0.0.0                 | Server host                                  |
| `PORT`             | 8000                    | Server port                                  |
| `SECRET_KEY`       | (default)               | Secret key for security                      |
| `ALLOWED_HOSTS`    | ["*"]                   | CORS allowed hosts                           |
| `DATABASE_URL`     | sqlite:///./app.db      | Database connection URL                      |
| `LOG_LEVEL`        | INFO                    | Logging level (DEBUG/INFO/WARNING/ERROR)     |
| `JSON_LOGS`        | false                   | Enable JSON logging format                   |
| `EXTERNAL_API_KEY` | ""                      | External API key                             |
| `EXTERNAL_API_URL` | https://api.example.com | External API URL                             |
| `ENABLE_CORS`      | true                    | Enable CORS middleware                       |

#### Example Environment Files

**Development (.env.development):**

```bash
APP_NAME="Minimal FastAPI App (Dev)"
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
JSON_LOGS=false
```

**Production (.env.production):**

```bash
APP_NAME="Minimal FastAPI App"
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=WARNING
JSON_LOGS=true
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=["yourdomain.com", "www.yourdomain.com"]
ENABLE_CORS=false
```

### Using Settings in Code

```python
from minimal_fastapi_app.core.config import settings

# Access any setting
print(f"App running in {settings.environment} mode")
print(f"Debug mode: {settings.debug}")
print(f"Database URL: {settings.database_url}")

# Settings are validated by pydantic
```

### Ruff Configuration

Add to your `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I"]  # Basic linting rules
```

### nginx Configuration

The `nginx.conf` includes:

- Reverse proxy to FastAPI (port 8000 → 8001)
- Proper headers forwarding
- Connection pooling

## Architecture

### Application Structure

The application follows FastAPI best practices with module-based organization:

- **`main.py`** - Application factory, middleware, and exception handler registration
- **`core/`** - Shared functionality across the application
  - **`models.py`** - Shared Pydantic models (health checks, etc.)
  - **`config.py`** - Settings and configuration management
  - **`logging.py`** - Structured logging with structlog
  - **`middleware.py`** - Request/response middleware with correlation IDs
  - **`exceptions.py`** - Custom exception handlers with consistent error responses
- **`users/`** - Complete user feature module
  - **`models.py`** - User-specific Pydantic schemas
  - **`service.py`** - Business logic and data operations
  - **`router.py`** - HTTP endpoints and request handling

### Key Benefits

- **Feature isolation** - Each module is self-contained
- **Clear separation of concerns** - Models, business logic, and routes separated
- **Structured logging** - JSON logs in production, colored console in development
- **Request tracing** - Correlation IDs for request tracking across services
- **Consistent error handling** - Standardized error responses with proper logging
- **Easy testing** - Each layer can be tested independently
- **Scalable** - New features follow the same pattern
- **Maintainable** - Changes are localized to specific modules

### Observability Features

**Structured Logging:**

- Correlation IDs on every request
- JSON output in production, colored console in development
- Automatic request/response logging with timing
- Business logic events with context

**Error Handling:**

- Consistent error response format
- Detailed validation error messages
- Proper HTTP status codes
- Error correlation with request IDs

**Security:**

- Security headers middleware
- CORS configuration
- Input validation and sanitization

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_main.py         # API endpoint tests
```

### Sample Test

```python
import pytest
from fastapi.testclient import TestClient
from minimal_fastapi_app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World", "status": "running"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

## Production Considerations

### Security

- Non-root user in container
- Minimal base image (python:3.13-slim)
- nginx as reverse proxy
- Environment variable management

### Performance

- nginx for static files and load balancing
- Multiple FastAPI workers: `--workers 4`
- Connection pooling

### Monitoring

Consider adding:

- Health check endpoints
- Logging configuration
- Metrics collection
- Error tracking

## Troubleshooting

### Common Issues

**Port already in use**

```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Container build fails**

```bash
# Clean container cache
podman system prune -a
```

**Dependencies not found**

```bash
# Regenerate lock file
rm uv.lock
uv sync
```

**Permission errors in container**

```bash
# Make sure .dockerignore excludes .venv
echo ".venv/" >> .dockerignore
podman-compose down
podman-compose up -d --build
```

### Logs

```bash
# Application logs
podman-compose logs fastapi

# nginx logs
podman-compose logs nginx

# Follow logs in real-time
podman-compose logs -f
```

## Complete Development Workflow

```bash
# 1. Start development
uv run uvicorn minimal_fastapi_app.main:app --reload

# 2. Make changes to code

# 3. Run tests
uv run pytest

# 4. Format and lint
uv run ruff format .
uv run ruff check --fix .

# 5. Test in production-like environment
podman-compose up -d --build
curl http://localhost:8000/

# 6. Clean up
podman-compose down
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `uv run pytest`
5. Format and lint code: `uv run ruff format . && uv run ruff check --fix .`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
