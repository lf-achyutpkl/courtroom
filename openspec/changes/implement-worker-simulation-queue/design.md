## Context

The API service already owns public FastAPI routes and Postgres persistence. Redis/RQ background workers also live in the API service workspace, but run as separate processes. The agent service owns LangGraph runtime code and exposes `run_trial` as the internal execution contract.

## Goals / Non-Goals

**Goals:**
- Add a simple async start endpoint that records `pending` status and returns immediately.
- Keep queueing, worker execution, and result persistence modular inside one Python workspace.
- Keep LangGraph isolated from queue and database side effects.
- Provide testable protocol boundaries for repositories and queues.
- Support dependent-job chaining across stage-specific queues so later TTS work can extend the pipeline without another workspace split.

**Non-Goals:**
- Add a full job dashboard or polling API beyond the persisted run record.
- Add node-level progress callbacks from inside LangGraph.
- Introduce a new shared schema package before the interface is repeated across services.

## Decisions

### 1. Keep `/start-simulation` in `apps/api-service`

The API service owns public HTTP APIs. The endpoint validates the case file, creates a simulation run, enqueues a job, and returns a pending response.

### 2. Use a worker wrapper for LangGraph completion

The worker wrapper calls `agent_service.service.run_trial` and stores intermediate output on the simulation run. LangGraph returns domain output and does not receive queue writers or persistence callbacks.

### 3. Use dependent jobs instead of a completion queue

The API service enqueues a generation job on the LLM queue and a dependent persistence job on the DB queue. The first stage marks the run `running` and stores the generated result. The second stage, which only runs after generation succeeds, marks the run `completed`. Failures in either stage mark the run `failed`.

### 4. Store initial results as JSONB

The first table stores `result JSONB` and `error_message TEXT` so the contract can stabilize before extracting a stronger shared output table.

## Data Flow

1. Client posts `{ "case_file_id": UUID }` to `POST /start-simulation`.
2. API verifies the case file exists.
3. API inserts `simulation_runs.status = 'pending'`.
4. API enqueues `{ simulation_run_id, case_file_id }` to the `simulation_llm` queue and creates a dependent DB job on `simulation_db`.
5. LLM worker marks the run `running`, loads the case file, runs LangGraph, and stores the generated result on the run record.
6. DB worker reads the stored result and marks the simulation run `completed`.
7. Any worker-stage failure marks the run `failed` with an error message.

## Risks / Trade-offs

- Redis/RQ introduces local infrastructure. Mitigation: keep adapters thin and inject protocols in tests.
- Chained jobs across multiple queues are slightly harder to enqueue atomically. Mitigation: keep the enqueue adapter thin and use best-effort cleanup if the second enqueue fails.
- JSONB result storage is broad. Mitigation: treat it as a v1 persistence envelope until a stronger shared schema is needed.
