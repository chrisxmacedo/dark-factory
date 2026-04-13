FROM python:3.12-slim

WORKDIR /app

# Install uv (faster than pip install)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock .

# Install dependencies (frozen for reproducibility)
RUN uv sync --no-dev --frozen

# Copy source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Expose port
EXPOSE 8080

# Run with 2 workers for production load
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
