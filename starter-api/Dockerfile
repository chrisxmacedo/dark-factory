FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock* .

# Install dependencies
RUN uv sync --no-dev

# Copy source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Expose port
EXPOSE 8080

# Run
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
