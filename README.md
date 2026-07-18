# Courtroom Simulation

Multi-agent LangGraph courtroom simulator. RAG-grounded rulings, adversarial attorney agents, and verdicts that vary every run, played back as an animated trial with TTS and PixiJS.

## Tech

- Next.js
- React
- TypeScript
- PixiJS
- Python
- LangGraph
- OpenSpec

## Repository Shape

This is a polyglot monorepo:

- `apps/web-app` contains the Next.js playback frontend.
- `apps/api-service` contains the FastAPI backend API.
- `apps/api-service` also owns Redis/RQ background workers and queue orchestration.
- `apps/agent-service` contains LangGraph simulation runtime, prompts, and evaluation logic.
- `infra/db/migrations` contains shared Postgres schema migrations.
- `packages/contracts` is reserved for future shared contracts.
- `packages/python-domain` contains shared Python domain models used by multiple services.

Docker implementation is intentionally not included yet.

## Docker Deployment

The repository now includes a root Docker Compose stack that packages the current runtime boundaries:

- `web-app`
- `api-service`
- `worker-llm`
- `worker-tts`
- `postgres`
- `redis`

`agent-service` is not deployed as a separate HTTP container. It remains imported runtime code bundled into the Python image used by `api-service` and the worker processes.

### First-Time Setup

Create the service env files:

```bash
cp apps/web-app/.env.example apps/web-app/.env
cp apps/api-service/.env.example apps/api-service/.env
cp apps/agent-service/.env.example apps/agent-service/.env
```

Optionally create a root compose override file when you want to change shared ports or infrastructure defaults:

```bash
cp .env.compose.example .env
```

Update secrets before booting the stack:

- set `OPENAI_API_KEY` in `apps/agent-service/.env`
- set `R2_*` values in `apps/api-service/.env`
- adjust shared compose variables in root `.env` if needed

### Start the Stack

```bash
docker compose up --build
```

Or via the root Makefile:

```bash
make docker-up
```

The main local endpoints are:

- web app: `http://localhost:3000`
- API service: `http://localhost:8000`

## Root Commands

Use the root `Makefile` to delegate into each workspace:

```bash
make web-dev
make api-dev
make agent-dev
make worker-dev
make docker-up
```
