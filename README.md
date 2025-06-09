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

## Project Structure

```
minimal-fastapi-app/
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
│       │   └── middleware.py    # Request logging, correlation IDs
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
├── compose.yaml
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

## Observability & Error Handling

- **Structured Logging:**
  - OpenTelemetry with JSON logs in production, colored logs in dev
  - Correlation IDs on every request (in logs and error responses)
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
