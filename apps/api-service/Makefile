UV_CACHE_DIR ?= /tmp/uv-cache
REDIS_URL ?= redis://localhost:6379/0

.PHONY: check lint format-check typecheck dev test worker-all worker-llm worker-tts db-upgrade db-current db-revision

check: lint format-check typecheck

lint:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .

format-check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check .

typecheck:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pyright

dev:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run uvicorn api_service.main:app --reload

test:
	OPENAI_API_KEY=dummy UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m unittest discover -s tests -p "test_*.py"

worker-all:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m api_service.worker --url $(REDIS_URL) simulation_llm simulation_tts

worker-llm:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m api_service.worker --url $(REDIS_URL) simulation_llm

worker-tts:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m api_service.worker --url $(REDIS_URL) simulation_tts

db-upgrade:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run alembic upgrade head

db-current:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run alembic current

db-revision:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run alembic revision --autogenerate -m "$(MESSAGE)"
