.PHONY: help web-dev web-build web-start web-lint api-dev api-test agent-dev agent-test agent-eval-baseline agent-langgraph-dev worker-dev worker-llm worker-db

help:
	@echo "Available targets:"
	@echo "  web-dev              Start the Next.js web app"
	@echo "  web-build            Build the Next.js web app"
	@echo "  web-start            Start the built Next.js web app"
	@echo "  web-lint             Run web app linting"
	@echo "  api-dev              Start the FastAPI backend API"
	@echo "  api-test             Run API service tests"
	@echo "  agent-dev            Start the LangGraph dev server"
	@echo "  agent-test           Run agent-service tests"
	@echo "  agent-eval-baseline  Run the agent baseline evaluation"
	@echo "  worker-dev           Start API-owned background workers"
	@echo "  worker-llm           Start the simulation LLM worker"
	@echo "  worker-db            Start the simulation DB worker"

web-dev:
	pnpm --dir apps/web-app dev

web-build:
	pnpm --dir apps/web-app build

web-start:
	pnpm --dir apps/web-app start

web-lint:
	pnpm --dir apps/web-app lint

api-dev:
	$(MAKE) -C apps/api-service dev

api-test:
	$(MAKE) -C apps/api-service test

agent-dev:
	$(MAKE) -C apps/agent-service langgraph-dev

agent-test:
	$(MAKE) -C apps/agent-service test

agent-eval-baseline:
	$(MAKE) -C apps/agent-service eval-baseline

worker-dev:
	$(MAKE) -C apps/api-service worker-all

worker-llm:
	$(MAKE) -C apps/api-service worker-llm

worker-db:
	$(MAKE) -C apps/api-service worker-db
