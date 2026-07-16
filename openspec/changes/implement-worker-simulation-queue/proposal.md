## Why

Simulation runs should not execute inside the request/response path. The API needs a small public endpoint that records a requested simulation, enqueues the work, and returns immediately while background worker processes run LangGraph and persist the final result asynchronously.

## What Changes

- Add `POST /start-simulation` to the API service.
- Persist simulation run status in a new `simulation_runs` table.
- Add Redis/RQ queue adapters for chained simulation pipeline jobs inside `apps/api-service`.
- Execute worker stages from `apps/api-service` through separate RQ worker commands instead of a standalone `worker-service` workspace.
- Keep LangGraph queue-agnostic while the API-owned worker stages orchestrate dependent jobs across LLM and persistence queues.

## Capabilities

### New Capabilities

- `simulation-run-queue`: Start simulations asynchronously, track run status, execute queued LangGraph work, and complete dependent persistence stages through a chained job pipeline.

### Modified Capabilities

- None.

## Impact

- Affects `apps/api-service`, `apps/agent-service` integration, and database migrations.
- Adds Redis/RQ as the queue mechanism for API-to-worker simulation jobs.
- Adds a new database table for simulation run tracking.
- Removes the separate `apps/worker-service` workspace in favor of API-owned worker entrypoints.
