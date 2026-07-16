# API Service

FastAPI backend API workspace for the courtroom simulator.

## Responsibilities

- expose backend HTTP APIs
- persist normal application data in Postgres
- own Redis/RQ background job pipelines and worker entrypoints
- call the agent service through an internal contract rather than owning LangGraph graph code

## Local Development

Apply database migrations from `../../infra/db/migrations/`, then create a local environment file:

```bash
cp .env.example .env
```

Update `DATABASE_URL` in `.env` if you are not using the local default.
Set `REDIS_URL` when using a non-default Redis instance for background jobs.
Set the `R2_*` variables and `TTS_PROVIDER` before starting the audio worker.

Start the API service with:

```bash
make dev
```

Run background workers from the same workspace:

```bash
make worker-all
```

Or start queue-specific workers:

```bash
make worker-llm
make worker-tts
```

The simulation pipeline now runs in two worker-owned stages:

1. `simulation_llm` generates the trial result, stores it immediately, and marks the run `hearing_completed`
2. `simulation_tts` marks the run `generating_audio`, synthesizes speech, uploads turn audio to Cloudflare R2, and only then marks the run `completed`

The current case file API exposes:

- `POST /case-files` to create and store a new dummy `CaseFile`
- `GET /case-files/{id}` to fetch a stored `CaseFile` by storage UUID
- `POST /start-simulation` to create a pending simulation run and enqueue it
  for the simulation pipeline

## Tests

```bash
make test
```

## Shared Models

The API imports `CaseFile` from the shared `courtroom-domain` package in `../../packages/python-domain`.

## Code Layout

- `src/api_service/main.py` is the application composition root
- `src/api_service/api/routers/` contains HTTP route modules
- `src/api_service/api/deps.py` contains shared dependency providers
- `src/api_service/schemas/` contains request and response models
- `src/api_service/db/` contains database session and ORM base definitions
- `src/api_service/queue/` contains Redis/RQ queue adapters and pipeline enqueueing
- `src/api_service/repositories/` contains persistence adapters
- `src/api_service/services/` contains application and integration services
- `src/api_service/jobs/` contains RQ-callable entrypoints
- `src/api_service/workflows/` contains background workflow orchestration
