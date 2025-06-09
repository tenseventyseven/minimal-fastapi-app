# Minimal FastAPI App

A production-grade, minimal FastAPI application using modern Python tooling, clear patterns, and containerized deployment. This project demonstrates best practices for scalable, maintainable, and observable API services.

## Features

- **FastAPI** for high-performance APIs
- **Pydantic** for data validation and settings
- **pydantic-settings** for environment-based config
- **SQLAlchemy (async)** for database access
- **uv** for dependency management and scripts
- **Hatchling** for builds
- **Docker/Podman** for containers
- **nginx** as a production reverse proxy
- **pytest** for testing
- **ruff** for linting/formatting
- **OpenTelemetry logging** for structured, traceable logs (JSON in production, colored in dev)
- **Alembic-ready migrations/** folder for future database schema management

## Project Structure

```
minimal-fastapi-app/
├── migrations/           # Alembic (or similar) DB migrations (placeholder)
├── src/
│   └── minimal_fastapi_app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app factory, middleware, handlers
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py        # Settings/config
│       │   ├── db.py            # SQLAlchemy base/session
│       │   ├── exceptions.py    # Custom error types/handlers
│       │   ├── logging.py       # OpenTelemetry setup
│       │   └── middleware.py    # Request logging, trace IDs
│       ├── users/
│       │   ├── __init__.py
│       │   ├── models.py        # SQLAlchemy ORM
│       │   ├── schemas.py       # Pydantic schemas
│       │   ├── service.py       # Business logic
│       │   └── router.py        # API endpoints
│       └── projects/
│           ├── models.py
│           ├── schemas.py
│           ├── service.py
│           └── router.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_users.py
│   ├── test_projects.py
│   ├── test_project_user_endpoints.py
│   └── test_user_project.py
├── Dockerfile
├── dev.Dockerfile
├── compose.yaml
├── compose.override.yaml
├── nginx.conf
├── pyproject.toml
├── uv.lock
├── .env.example
├── .env.development
├── .env.production
├── pytest.ini
└── README.md
```

## Quick Start

1. **Clone and Install**
   ```bash
   git clone <repo-url>
   cd minimal-fastapi-app
   uv sync
   cp .env.example .env
   # Edit .env as needed
   ```
2. **Run in Development**
   ```bash
   uv run uvicorn minimal_fastapi_app.main:app --reload
   ```
3. **Run Tests**
   ```bash
   uv run pytest
   ```
4. **Lint & Format**
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   ```
5. **Production Build (Docker/Podman)**
   ```bash
   podman-compose up -d --build
   # or
   docker-compose up -d --build
   # App at http://localhost:8000
   ```

## API Endpoints (Users)

| Method | Endpoint         | Description            |
| ------ | ---------------- | ---------------------- |
| GET    | `/`              | Root welcome/status    |
| GET    | `/health`        | Health check           |
| GET    | `/info`          | App info/config        |
| POST   | `/v1/users/`     | Create user            |
| GET    | `/v1/users/`     | List users (paginated) |
| GET    | `/v1/users/{id}` | Get user by ID         |
| PUT    | `/v1/users/{id}` | Update user            |
| DELETE | `/v1/users/{id}` | Delete user            |

Projects endpoints follow a similar pattern under `/v1/projects/`.

## Configuration

- Uses `.env` files and environment variables (see `.env.example`)
- All config validated by Pydantic
- Example variables: `APP_NAME`, `DEBUG`, `DATABASE_URL`, `LOG_LEVEL`, `ALLOWED_HOSTS`, etc.
- **Override config for local/dev/test:**
  - Copy `.env.example` to `.env` and edit as needed for local development.
  - Use `.env.development` for development-specific overrides (auto-loaded if present).
  - Use `.env.production` for production deployments (see Dockerfile for usage).
  - You can also set environment variables directly in your shell or CI/CD pipeline to override any setting.
  - For tests, you can set environment variables using `monkeypatch` in pytest or by exporting them before running tests.

## Observability & Error Handling

- **Structured Logging:**
  - OpenTelemetry with JSON logs in production, colored logs in dev
  - Trace IDs (from OpenTelemetry) on every request (in logs and error responses)
- **Error Handling:**
  - Consistent JSON error format for validation, business, and HTTP errors
  - Custom `BusinessException` for domain errors
- **Security:**
  - Security headers middleware
  - CORS configurable
  - Input validation everywhere

## Testing

- All tests in `tests/` (pytest)
- Fixtures for DB isolation
- Example test:
  ```python
  def test_read_root():
      response = client.get("/")
      assert response.status_code == 200
      assert response.json()["message"] == "Hello World"
  ```

## Running Tests & Linting

### Run All Tests

Use [pytest](https://docs.pytest.org/) to run all tests:

```bash
uv run pytest
```

Or run a specific test file:

```bash
uv run pytest tests/test_users.py
uv run pytest tests/test_projects.py
```

### Linting & Formatting

Use [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
uv run ruff format .           # Format all code
uv run ruff check --fix .      # Lint and auto-fix issues
```

You can also run both in one line:

```bash
uv run ruff format . && uv run ruff check --fix .
```

- All test and lint commands work in both local and containerized environments.
- See `pytest.ini` and `pyproject.toml` for configuration details.

## Development & Maintenance

- **Add dependencies:** `uv add <package>`
- **Update:** `uv sync`
- **Format/lint:** `uv run ruff format . && uv run ruff check --fix .`
- **Build:** `uv build`
- **Run tests:** `uv run pytest`
- **Run in Docker:** `podman-compose up -d --build`

## Production Considerations

- Runs as non-root in container
- Minimal base image (python:3.13-slim)
- nginx as reverse proxy
- Multiple FastAPI workers supported
- Connection pooling for DB
- Health, info, and metrics endpoints
- **Database migrations recommended:** Use Alembic for schema changes (see `migrations/`)

## Security & Production Hardening

- **CORS:** Configurable via environment and enforced in FastAPI (see `main.py`).
- **Rate Limiting:** Not enabled by default. For production, consider adding a rate limiting middleware such as [slowapi](https://pypi.org/project/slowapi/) or [starlette-limiter](https://pypi.org/project/starlette-limiter/). Example:

  ```python
  # In main.py
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address
  from fastapi import FastAPI

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
  # Then use @limiter.limit("5/minute") on endpoints
  ```

- **HTTPS:**
  - In production, always run behind a reverse proxy (e.g., nginx) that terminates TLS/SSL.
  - See `nginx.conf` for an example. For local testing, you can use [mkcert](https://github.com/FiloSottile/mkcert) or self-signed certs with uvicorn's `--ssl-keyfile` and `--ssl-certfile` options.
  - Example nginx snippet:
    ```nginx
    server {
        listen 443 ssl;
        ssl_certificate /etc/ssl/certs/your.crt;
        ssl_certificate_key /etc/ssl/private/your.key;
        ...
    }
    ```
- **Other Recommendations:**
  - Set `SECURE_PROXY_SSL_HEADER` if behind a proxy.
  - Use strong, unique `SECRET_KEY` in production (enforced by config).
  - Regularly update dependencies and review security advisories.

## Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `uv run pytest`
5. Format/lint: `uv run ruff format . && uv run ruff check --fix .`
6. Commit: `git commit -am 'Add feature'`
7. Push: `git push origin feature-name`
8. Open a pull request

## License

MIT License. See `LICENSE` file for details.

## Development Notes

- **dev.Dockerfile** and **compose.override.yaml** are provided for local development:
  - Use `dev.Dockerfile` for a hot-reloading, development-friendly container.
  - Use `docker-compose -f compose.yaml -f compose.override.yaml up` to start the app in development mode with code reloading and local `.env.development`.

## Trace/Log Correlation Example

All logs and error responses include the OpenTelemetry trace ID for easy correlation between API requests, logs, and distributed traces.

**Example error response:**

```json
{
  "error": "business_error",
  "message": "A project with this name already exists",
  "details": [
    {
      "field": "name",
      "message": "Project name is already in use",
      "code": "name_exists"
    }
  ],
  "trace_id": "b7e23ec29af22b0b4e41da31e868d572"
}
```

**Example log entry (JSON):**

```json
{
  "timestamp": "2025-06-09T12:34:56.789Z",
  "level": "warning",
  "event": "Failed to create project due to duplicate name",
  "name": "minimal_fastapi_app.projects.service",
  "trace_id": "b7e23ec29af22b0b4e41da31e868d572",
  "span_id": "e41da31e868d5721",
  "name": "Project Alpha"
}
```

- The `trace_id` is present in both the API response and the logs, making it easy to correlate requests and logs in distributed systems or observability platforms.
- In development, logs are colorized; in production, logs are JSON for easy ingestion by log management tools.

## How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd minimal-fastapi-app
   ```
2. **Install dependencies:**
   ```bash
   uv sync
   cp .env.example .env
   # Edit .env as needed for your environment
   ```
3. **Run the app in development mode:**
   ```bash
   uv run uvicorn minimal_fastapi_app.main:app --reload
   # App will be available at http://localhost:8000
   ```
4. **Run tests:**
   ```bash
   uv run pytest
   ```
5. **Lint & format:**
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   ```

## How to Deploy

### Docker/Podman (Recommended for Production)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   # or
   podman-compose up -d --build
   # App will be available at http://localhost:8000
   ```
2. **Production environment:**
   - Edit `.env.production` for production settings (see `.env.example` for options).
   - The `Dockerfile` and `nginx.conf` are set up for production best practices (non-root, port 8000, static files, reverse proxy, etc).
   - For local development with hot-reloading, use:
     ```bash
     docker-compose -f compose.yaml -f compose.override.yaml up
     ```
3. **HTTPS:**
   - In production, always run behind a reverse proxy (e.g., nginx) that terminates TLS/SSL.
   - See the README section on HTTPS for more details and example nginx config.
