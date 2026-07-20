DOCKER_COMPOSE ?= $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

.PHONY: help web-dev web-build web-start web-lint api-dev api-test api-db-upgrade api-db-current api-db-revision agent-dev agent-test agent-eval-baseline agent-langgraph-dev worker docker-up docker-down docker-logs

help:
	@echo "Available targets:"
	@echo "  web-dev              Start the Next.js web app"
	@echo "  web-build            Build the Next.js web app"
	@echo "  web-start            Start the built Next.js web app"
	@echo "  web-lint             Run web app linting"
	@echo "  api-dev              Start the FastAPI backend API"
	@echo "  api-test             Run API service tests"
	@echo "  api-db-upgrade       Apply database migrations"
	@echo "  api-db-current       Show the current database revision"
	@echo "  api-db-revision      Generate a new Alembic revision with MESSAGE=..."
	@echo "  agent-dev            Start the LangGraph dev server"
	@echo "  agent-test           Run agent-service tests"
	@echo "  agent-eval-baseline  Run the agent baseline evaluation"
	@echo "  worker               Start all API-owned background workers"
	@echo "  docker-up            Start the Docker Compose stack"
	@echo "  docker-down          Stop the Docker Compose stack"
	@echo "  docker-logs          Follow Docker Compose logs"

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

api-db-upgrade:
	$(MAKE) -C apps/api-service db-upgrade

api-db-current:
	$(MAKE) -C apps/api-service db-current

api-db-revision:
	$(MAKE) -C apps/api-service db-revision MESSAGE="$(MESSAGE)"

agent-dev:
	$(MAKE) -C apps/agent-service langgraph-dev

agent-test:
	$(MAKE) -C apps/agent-service test

agent-eval-baseline:
	$(MAKE) -C apps/agent-service eval-baseline

worker:
	$(MAKE) -C apps/api-service worker-all

docker-up:
	$(DOCKER_COMPOSE) up --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f
