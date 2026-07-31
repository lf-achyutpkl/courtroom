UV_CACHE_DIR ?= /tmp/uv-cache

.PHONY: check lint format-check typecheck test langgraph-dev

check: lint format-check typecheck test

lint:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .

format-check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check .

typecheck:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pyright --project pyproject.toml

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pytest

langgraph-dev:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run langgraph dev
