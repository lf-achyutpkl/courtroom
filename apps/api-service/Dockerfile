FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV PATH=/app/apps/api-service/.venv/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/python-domain ./packages/python-domain
COPY apps/agent-service ./apps/agent-service
COPY apps/api-service ./apps/api-service

WORKDIR /app/apps/api-service

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
