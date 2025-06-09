FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Change ownership of /app to app user
RUN chown app:app /app

# Switch to app user before installing dependencies
USER app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Copy only source code and README (needed for hatchling build)
COPY src/ src/
COPY README.md ./

# Copy production environment file
COPY .env.production .env

# Install dependencies without building the package
RUN uv sync --frozen --no-cache --no-install-project

# Expose port
EXPOSE 8000

# Run with uvicorn via uv
CMD ["uv", "run", "uvicorn", "minimal_fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000"]