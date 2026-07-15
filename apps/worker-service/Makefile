UV_CACHE_DIR ?= /tmp/uv-cache
REDIS_URL ?= redis://localhost:6379/0

.PHONY: dev completion-worker test

dev:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run rq worker --url $(REDIS_URL) simulation_jobs

completion-worker:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run rq worker --url $(REDIS_URL) simulation_results

test:
	OPENAI_API_KEY=dummy UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m unittest discover -s tests -p "test_*.py"
