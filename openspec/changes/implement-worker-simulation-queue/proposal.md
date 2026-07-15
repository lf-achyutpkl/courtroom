## Why

Simulation runs should not execute inside the request/response path. The API needs a small public endpoint that records a requested simulation, enqueues the work, and returns immediately while a worker process runs LangGraph and persists the final result asynchronously.

## What Changes

- Add `POST /start-simulation` to the API service.
- Persist simulation run status in a new `simulation_runs` table.
- Add Redis/RQ queue adapters for simulation jobs and completion messages.
- Implement the initial worker-service runtime that executes LangGraph through the agent-service contract.
- Keep LangGraph queue-agnostic by publishing completion messages from the worker wrapper after graph execution returns.

## Capabilities

### New Capabilities

- `simulation-run-queue`: Start simulations asynchronously, track run status, execute queued LangGraph work, and write completed or failed results back through a completion queue.

### Modified Capabilities

- None.

## Impact

- Affects `apps/api-service`, `apps/worker-service`, `apps/agent-service` integration, and database migrations.
- Adds Redis/RQ as the queue mechanism for API-to-worker simulation jobs.
- Adds a new database table for simulation run tracking.
