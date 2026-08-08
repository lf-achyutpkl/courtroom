## Context

`apps/agent-service` owns the AI-vs-human LangGraph and currently exposes it through a Studio-only file entrypoint. Its human-attorney nodes pause with `interrupt()` and accept a base64 audio payload for Deepgram transcription. `apps/api-service` already owns the public FastAPI boundary, PostgreSQL, Redis/RQ workers, and an R2-backed object-storage abstraction for generated simulation audio. `apps/web-app` proxies API calls through Next.js route handlers and has no recording flow.

The new flow must give a browser user a small, durable way to participate without carrying a long-running graph invocation or audio bytes through an HTTP request. Existing AI-vs-AI simulation runs and their generated-audio pipeline remain independent.

## Goals / Non-Goals

**Goals:**

- Create, inspect, and resume an AI-vs-human run through public API endpoints.
- Preserve each run across worker retries by using a stable LangGraph thread/checkpoint identity.
- Store participant recordings in Cloudflare R2 and retain immutable object metadata, not base64 payloads, in PostgreSQL.
- Use Redis/RQ for graph execution/resumption, R2 verification/download, transcription-triggering payload preparation, and state persistence.
- Provide a basic browser page that selects a case and side, polls state, records audio with `MediaRecorder`, uploads it, and submits the expected turn.

**Non-Goals:**

- Rebuild the existing AI-vs-AI simulation library, playback screen, or TTS pipeline.
- Provide live streaming, websocket events, rich trial controls, authentication/authorization, or collaborative participants.
- Expose R2 credentials or route recording bytes through the Next.js or FastAPI request body.
- Add a new worker workspace or move LangGraph orchestration into the web app or API request handlers.

## Decisions

### 1. Use a dedicated interactive-run resource and endpoints

The API will expose an `interactive-trial-runs` resource rather than extending `/start-simulation` and `simulation_runs`. A run is created with a `case_file_id` and `human_attorney_side`; the initial graph invocation is queued. A detail endpoint returns the current status, transcript, terminal result when available, and a normalized pending-human-turn descriptor. The API will reject response submissions that do not match that descriptor.

This keeps the existing one-shot AI-vs-AI status model stable and makes the pause/resume state explicit. Reusing `simulation_runs` was considered, but its schema and RQ chain represent a one-way generated-audio pipeline rather than repeated participant turns.

### 2. Make the interactive graph checkpointable through its service contract

`apps/agent-service` will expose an API-worker-facing interactive execution function that compiles/invokes the interactive graph with a supplied durable checkpointer and a `thread_id`. New runs invoke the graph with initial state; response jobs resume it with `Command(resume=...)`. The worker reads the resulting state/interrupt and maps it into the API-owned persistence record.

The graph continues to own attorney behavior, turn ordering, Deepgram transcription, and transcript construction. Persisting raw graph internals in the API instead of using LangGraph checkpoints was considered, but would duplicate checkpoint semantics and make retries unsafe.

### 3. Model participant turns and run state in API-owned PostgreSQL records

New tables/records will distinguish the interactive run from each expected response. The run stores its ID, case-file ID, human side, LangGraph thread ID, status (`queued`, `running`, `awaiting_human`, `completed`, `failed`), transcript/result snapshot, current pending-turn identity, error, and lifecycle timestamps. A participant-turn record stores the expected scene/side, a monotonic turn/attempt identifier, upload state, R2 bucket/key/content type/size/checksum, and submission/job timestamps.

The repository will enforce one active pending turn per run and a state transition sequence that makes duplicate browser submits and RQ retries idempotent. JSON snapshots are intentionally used for the evolving graph output, matching the existing simulation-run persistence approach.

### 4. Upload recordings directly to private R2 objects with scoped presigned URLs

When a run is awaiting a human turn, the browser requests an upload authorization for that exact turn. The API creates or reuses the turn attempt and returns a short-lived presigned `PUT` URL, required headers, object key, and expiry. It permits only supported audio MIME types, applies a configured maximum byte size, and derives an opaque key such as `interactive-trial-runs/{run-id}/turns/{turn-id}/recording.{extension}`.

After the browser uploads, it calls a submit endpoint. The API uses its R2 client to verify object existence, MIME type, and size before enqueuing the resume job. The RQ job downloads the object using service credentials, base64-encodes it only in memory, and supplies the existing graph resume payload. Participant audio objects are private; worker access uses R2 credentials, so the existing public URL convention for generated TTS artifacts is not reused.

Direct upload avoids API/Next.js body limits and makes retries practical. Proxying audio through FastAPI was considered but would make request lifetime and bandwidth a public API bottleneck.

### 5. Reuse the API-service RQ worker with a separate interactive queue

The API service adds an `interactive_trial` queue adapter and job module. Jobs include initial graph execution and response resumption; both perform repository state transitions, call the agent-service contract, and store the next snapshot. They are idempotent by run ID plus participant-turn ID. Failures transition the run to `failed` with a safe user-facing message and retain diagnostic detail in logs.

The existing `simulation_llm`/`simulation_tts` chained queues are not repurposed, because an interactive run has user-paced, repeated resumes rather than a fixed dependency chain. A distinct queue allows worker concurrency and retry policy to be tuned independently.

### 6. Add a minimal isolated Next.js participation page

The web app adds an AI-vs-human entry route and route handlers that proxy the new API endpoints. The client selects an existing case and human side, creates a run, polls the detail endpoint while work is in progress, displays a plain transcript/status, and enables a recorder only during `awaiting_human`. It requests upload authorization, uploads the resulting `Blob` directly to R2, then submits the turn and resumes polling.

The initial UI deliberately has no playback timeline, waveform, rich editor, or optimistic transcript synthesis. Browser permission denial, unsupported recording, upload failure, and failed run states receive clear retry/error messaging.

## Risks / Trade-offs

- [A worker crash after graph progress but before snapshot persistence] → Use the stable thread ID/checkpointer and idempotent jobs; retry reads graph state before advancing repository state.
- [Duplicate uploads or submit clicks] → Bind each upload to the active turn ID, verify current state transactionally, and treat an already queued/submitted matching turn as idempotent.
- [Untrusted client audio] → Use short expiry, exact object prefix/key, MIME/size validation, server-side `HEAD` verification, and private buckets; validate decoded data before transcription.
- [R2 CORS misconfiguration blocks browser upload] → Document required allowed origin, `PUT`, content-type, and exposed headers alongside environment configuration; cover it in deployment smoke tests.
- [Polling delays participant feedback] → Use a short, bounded polling interval and explicit queued/running labels; real-time transport remains out of scope.
- [Deepgram or graph failure after an upload] → Preserve the recording metadata for diagnosis, mark the run failed safely, and allow a future explicit retry flow rather than silently reusing audio.

## Migration Plan

1. Add the PostgreSQL migration, repository, configuration validation, R2 presigning/download support, and RQ queue/job registration behind the new routes.
2. Add the agent-service checkpointable execution contract and contract/unit tests.
3. Deploy API and workers with R2 CORS and private-object lifecycle rules configured, then deploy the web route.
4. Roll back by removing the web route and disabling the new API routes/workers; existing simulation-run tables, endpoints, and R2 generated-audio keys are unaffected. New interactive records and objects can be retained for support or removed by a lifecycle policy.

## Open Questions

- Which database/checkpointer deployment configuration will the API-service worker use for the LangGraph Postgres checkpointer, and whether it shares the API PostgreSQL URL or has a separately scoped connection string?
- What maximum recording duration/byte size and accepted browser MIME fallback set are appropriate for the initial rollout?
- What R2 retention policy is required for participant recordings, particularly failed or abandoned runs?
