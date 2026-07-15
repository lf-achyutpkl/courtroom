# Worker Service

RQ worker workspace for asynchronous courtroom simulation jobs.

## Responsibilities

- consume simulation jobs enqueued by the API service
- call the agent-service LangGraph runtime through its Python contract
- publish simulation completion messages to the results queue
- apply completion messages to the `simulation_runs` table

## Local Development

Apply database migrations from `../../infra/db/migrations/`, then create a local environment file:

```bash
cp .env.example .env
```

Start the simulation worker with:

```bash
make dev
```

Start the completion worker with:

```bash
make completion-worker
```

Both targets use `REDIS_URL`, defaulting to `redis://localhost:6379/0`.

## Tests

```bash
make test
```
