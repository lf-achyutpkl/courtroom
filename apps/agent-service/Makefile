UV_CACHE_DIR ?= /tmp/uv-cache

.PHONY: check lint format-check typecheck test unit-test langgraph-dev eval-baseline eval-baseline-rubric promptfoo-adversarial validate-promptfoo-suite

check: lint format-check typecheck

lint:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .

format-check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check .

typecheck:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pyright

test:
	OPENAI_API_KEY=dummy UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m unittest discover -s tests -p "test_*.py"

unit-test: test

langgraph-dev:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run langgraph dev

eval-baseline:
	OPENAI_API_KEY=$${OPENAI_API_KEY:-dummy} UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m src.evaluation.baseline

eval-baseline-rubric:
	OPENAI_API_KEY=$${OPENAI_API_KEY:?OPENAI_API_KEY is required for rubric evaluation} UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m src.evaluation.baseline --enable-rubric --rubric-judge-model gpt-5-nano

validate-promptfoo-suite:
	OPENAI_API_KEY=$${OPENAI_API_KEY:-dummy} UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m src.evaluation.promptfoo_suite

promptfoo-adversarial: validate-promptfoo-suite
	npx promptfoo@latest eval -c evals/promptfoo/promptfooconfig.json
