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
- `apps/agent-service` contains LangGraph simulation runtime, prompts, and evaluation logic.
- `apps/worker-service` is reserved for the future RQ/Redis worker process.
- `infra/db/migrations` contains shared Postgres schema migrations.
- `packages/contracts` is reserved for future shared contracts.
- `packages/python-domain` contains shared Python domain models used by multiple services.

Docker implementation is intentionally not included yet.

## Root Commands

Use the root `Makefile` to delegate into each workspace:

```bash
make web-dev
make api-dev
make agent-dev
make worker-dev
```
