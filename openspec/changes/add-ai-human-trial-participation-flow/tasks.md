## 1. Interactive runtime contract

- [x] 1.1 Add a checkpointable interactive-trial execution/resume service contract in `apps/agent-service` that accepts a stable thread ID, initializes graph state, resumes `interrupt()` values, and returns normalized state/interrupt output.
- [x] 1.2 Configure the interactive graph for durable Postgres checkpointing without changing the existing AI-vs-AI graph contract.
- [x] 1.3 Add unit tests for initial execution, resume from a persisted thread, human-side defaulting, and controlled invalid-audio/transcription failures. *(Deferred by user for now.)*

## 2. API persistence and R2 storage support

- [x] 2.1 Add a database migration and SQLAlchemy records for interactive trial runs and participant-turn attempts, including statuses, LangGraph thread ID, pending turn identity, result/transcript snapshot, R2 object metadata, timestamps, and errors.
- [x] 2.2 Implement interactive-run and participant-turn repositories with transactional state transitions and idempotency protections for concurrent or repeated submissions.
- [x] 2.3 Extend the R2 storage abstraction with presigned upload authorization, object metadata verification, and private-object download operations needed by workers.
- [x] 2.4 Add validated configuration for interactive recording MIME types, maximum size, upload expiry, R2 private-object use, and required browser-upload CORS deployment settings.
- [x] 2.5 Add repository and storage-adapter tests covering state transitions, stale turns, object verification failures, and no public URL exposure for participant audio. *(Deferred by user for now.)*

## 3. API routes and RQ orchestration

- [x] 3.1 Add dependency providers, Pydantic schemas, presenters, and FastAPI routes to create and retrieve `interactive-trial-runs`.
- [x] 3.2 Add endpoints to issue an active-turn upload authorization and submit a verified uploaded recording for that exact turn.
- [x] 3.3 Add an `interactive_trial` RQ queue adapter and worker jobs for initial execution and participant-turn resume, including retry-safe state transitions and safe failure handling.
- [x] 3.4 Integrate jobs with the agent-service checkpointed execution contract, preparing the existing Deepgram audio resume payload only in worker memory.
- [x] 3.5 Add API and job tests for valid creation, missing case files, awaiting-human status, successful resume, duplicate jobs/submits, stale turns, invalid R2 uploads, terminal runs, and worker failures. *(Deferred by user for now.)*

## 4. Basic web participation flow

- [x] 4.1 Add Next.js API route handlers that proxy every interactive-trial endpoint and preserve upload-authorisation response headers/body required by the browser.
- [x] 4.2 Add an isolated AI-vs-human trial page with case-file selection, human-side selection, run creation, plain status/transcript/result display, and bounded polling.
- [x] 4.3 Implement a client recording hook/component using `MediaRecorder`, including permission/unsupported-browser/error states and MIME selection compatible with the API contract.
- [x] 4.4 Implement direct R2 blob upload using the issued authorization, then submit the active turn and resume polling; do not send recording bytes through a Next.js server route.
- [x] 4.5 Add frontend tests for creation, queued/running/awaiting/completed/failed rendering, successful recording submission, denied permission, upload failure, and stale turn handling. *(Deferred by user for now.)*

## 5. Integration, documentation, and verification

- [x] 5.1 Document the public API payloads, RQ worker queue configuration, agent-service ownership boundary, R2 key/retention policy, and required R2 CORS settings.
- [x] 5.2 Add an end-to-end integration test with mocked R2, checkpointed graph execution, RQ jobs, and browser-facing API responses for a complete multi-turn run. *(Deferred by user for now.)*
- [x] 5.3 Run API-service, agent-service, and web-app checks; run `openspec validate add-ai-human-trial-participation-flow --strict`; update the OpenSpec checklist with the executed verification results. *(Executed: agent-service 58 tests passing; api-service 31 tests passing; web production build passing; strict OpenSpec validation passing.)*
