# Development Dockerfile for local use

# Start from the main Dockerfile as base
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

RUN chown app:app /app
USER app

COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY README.md ./
COPY .env.development .env

RUN uv sync --no-cache --no-install-project

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "minimal_fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
