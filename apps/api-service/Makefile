UV_CACHE_DIR ?= /tmp/uv-cache

.PHONY: dev test

dev:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run uvicorn api_service.main:app --reload

test:
	OPENAI_API_KEY=dummy UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m unittest discover -s tests -p "test_*.py"
