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

## Package Layout

The worker service should follow a conventional Python service layout so the
responsibility of each module is obvious at a glance:

```text
src/worker_service/
├── __init__.py
├── main.py                  # process entrypoint / worker bootstrap
├── core/                    # configuration, environment, process settings
│   ├── __init__.py
│   └── config.py
├── db/                      # SQLAlchemy base, engine, and session helpers
│   ├── __init__.py
│   ├── base.py
│   └── session.py
├── models/                  # worker-local job/message payloads
│   ├── __init__.py
│   ├── jobs.py
│   └── completions.py
├── orm/                     # SQLAlchemy table mappings
│   ├── __init__.py
│   └── records.py
├── repositories/            # persistence adapters for reads/writes
│   ├── __init__.py
│   ├── case_files.py
│   └── simulation_runs.py
├── queues/                  # Redis/RQ queue adapters
│   ├── __init__.py
│   ├── simulation_jobs.py
│   └── simulation_results.py
├── services/                # orchestration and application services
│   ├── __init__.py
│   ├── simulation_runner.py
│   └── completion_handler.py
└── jobs/                    # RQ job entrypoints / thin wrappers
    ├── __init__.py
    ├── simulation.py
    └── completion.py
```

### Boundary semantics

- `core/` owns process configuration only. It should not import repositories or queues.
- `db/` owns SQLAlchemy setup and engine/session lifecycle helpers.
- `models/` owns pure message objects and typed payloads used across the worker.
- `orm/` owns table mappings only. It should not contain queue or service logic.
- `repositories/` owns database reads and writes behind protocols.
- `queues/` owns Redis/RQ wiring and should remain thin adapters.
- `services/` owns orchestration, retries, and state transitions.
- `jobs/` owns the RQ callable entrypoints and should stay minimal.

## Current Migration Plan

The current `utils/` package is functional but not a good long-term shape for a
service that will grow. The migration should keep behavior stable while making
the codebase read like a standard Python application.

### File-by-file migration map

| Current file | Target file | Notes |
| --- | --- | --- |
| `src/worker_service/main.py` | `src/worker_service/main.py` | Keep as the process entrypoint; move worker bootstrap logic here if introduced. |
| `src/worker_service/utils/config.py` | `src/worker_service/core/config.py` | Environment loading and settings belong in `core/`. |
| `src/worker_service/utils/db.py` | `src/worker_service/db/session.py` | SQLAlchemy engine/session setup belongs in `db/`. |
| `src/worker_service/utils/models.py` | `src/worker_service/models/jobs.py` and `src/worker_service/models/completions.py` | Split transport payloads by responsibility. |
| `src/worker_service/utils/orm.py` | `src/worker_service/orm/records.py` | SQLAlchemy table mappings belong in `orm/`. |
| `src/worker_service/utils/repositories.py` | `src/worker_service/repositories/case_files.py` and `src/worker_service/repositories/simulation_runs.py` | Separate read/write adapters by aggregate. |
| `src/worker_service/utils/queues.py` | `src/worker_service/queues/simulation_results.py` | Keep Redis/RQ enqueue adapters in `queues/`. |
| `src/worker_service/utils/completion.py` | `src/worker_service/jobs/completion.py` | Keep the callable entrypoint thin; delegate to a service. |
| `src/worker_service/utils/runner.py` | `src/worker_service/services/simulation_runner.py` | Trial orchestration belongs in a service layer. |
| `src/worker_service/utils/jobs.py` | `src/worker_service/jobs/simulation.py` | Job entrypoints should only translate raw arguments into typed requests. |

### Suggested implementation order

1. Create the new package directories and `__init__.py` files.
2. Move `config.py`, `db.py`, and ORM definitions first so imports have a stable base.
3. Split payload models into `models/`.
4. Relocate repository and queue adapters.
5. Introduce `services/` and keep orchestration there.
6. Replace the old `utils/` imports with the new module paths.
7. Remove `utils/` once all references have been migrated and tests pass.

### Outcome

After migration, a Python developer should be able to answer these questions
without opening unrelated files:

- Where does environment configuration live?
- Where are database mappings and sessions defined?
- Which modules are queue adapters versus orchestration?
- Which files are safe to call from RQ as job entrypoints?
- Which layer owns persistence logic and which layer only coordinates work?
