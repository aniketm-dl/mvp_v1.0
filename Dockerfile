# Multi-stage build for reproducible image
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/
# Pre-copy deps to leverage cache
RUN pip install --upgrade pip && pip install -e .

# Now copy source
COPY . /app

# Runtime
EXPOSE 8000
ENV HOST=0.0.0.0 PORT=8000
# Admin token can be overridden at runtime
ENV ADMIN_TOKEN=changeme
# CORS default (comma-separated)
ENV CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# Rate limit default
ENV RATE_LIMIT_REQS_PER_MIN=120

CMD ["uvicorn", "src.api.service:app", "--host", "0.0.0.0", "--port", "8000"]
