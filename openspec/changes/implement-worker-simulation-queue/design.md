## Context

The API service already owns public FastAPI routes and Postgres persistence. The worker service is reserved for Redis/RQ background workers. The agent service owns LangGraph runtime code and exposes `run_trial` as the internal execution contract.

## Goals / Non-Goals

**Goals:**
- Add a simple async start endpoint that records `pending` status and returns immediately.
- Keep queueing, worker execution, and result persistence modular.
- Keep LangGraph isolated from queue and database side effects.
- Provide testable protocol boundaries for repositories and queues.

**Non-Goals:**
- Add a full job dashboard or polling API beyond the persisted run record.
- Add node-level progress callbacks from inside LangGraph.
- Introduce a new shared schema package before the interface is repeated across services.

## Decisions

### 1. Keep `/start-simulation` in `apps/api-service`

The API service owns public HTTP APIs. The endpoint validates the case file, creates a simulation run, enqueues a job, and returns a pending response.

### 2. Use a worker wrapper for LangGraph completion

The worker wrapper calls `agent_service.service.run_trial` and publishes either a success or failure message to the completion queue. LangGraph returns domain output and does not receive queue writers or persistence callbacks.

### 3. Persist results through a completion queue

The simulation worker publishes completion messages to a second queue. A completion consumer updates `simulation_runs` to `completed` or `failed`.

### 4. Store initial results as JSONB

The first table stores `result JSONB` and `error_message TEXT` so the contract can stabilize before extracting a stronger shared output table.

## Data Flow

1. Client posts `{ "case_file_id": UUID }` to `POST /start-simulation`.
2. API verifies the case file exists.
3. API inserts `simulation_runs.status = 'pending'`.
4. API enqueues `{ simulation_run_id, case_file_id }` to `simulation_jobs`.
5. Simulation worker marks the run `running`, loads the case file, runs LangGraph, and publishes a completion message.
6. Completion consumer writes the final result or failure to `simulation_runs`.

## Risks / Trade-offs

- Redis/RQ introduces local infrastructure. Mitigation: keep adapters thin and inject protocols in tests.
- The completion consumer is an extra moving part. Mitigation: make payloads small and database updates idempotent by run id.
- JSONB result storage is broad. Mitigation: treat it as a v1 persistence envelope until a stronger shared schema is needed.
