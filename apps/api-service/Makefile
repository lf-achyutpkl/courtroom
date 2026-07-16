UV_CACHE_DIR ?= /tmp/uv-cache
REDIS_URL ?= redis://localhost:6379/0

.PHONY: dev test worker-all worker-llm worker-tts

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
