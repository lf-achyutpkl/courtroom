UV_CACHE_DIR ?= /tmp/uv-cache

.PHONY: test unit-test

test:
	OPENAI_API_KEY=dummy UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m unittest discover -s tests -p "test_*.py"

unit-test: test
