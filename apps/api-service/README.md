# API Service

FastAPI backend API workspace for the courtroom simulator.

## Responsibilities

- expose backend HTTP APIs
- persist normal application data in Postgres
- enqueue background work through Redis/RQ once the worker service is implemented
- call the agent service through an internal contract rather than owning LangGraph graph code

## Local Development

Apply database migrations from `../../infra/db/migrations/`, then create a local environment file:

```bash
cp .env.example .env
```

Update `DATABASE_URL` in `.env` if you are not using the local default.
Set `REDIS_URL` when using a non-default Redis instance for background jobs.

Start the API service with:

```bash
make dev
```

The current case file API exposes:

- `POST /case-files` to create and store a new dummy `CaseFile`
- `GET /case-files/{id}` to fetch a stored `CaseFile` by storage UUID
- `POST /start-simulation` to create a pending simulation run and enqueue it
  for the worker service

## Tests

```bash
make test
```

## Shared Models

The API imports `CaseFile` from the shared `courtroom-domain` package in `../../packages/python-domain`.
