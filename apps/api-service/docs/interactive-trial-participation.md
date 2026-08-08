# Interactive trial participation contract

Run creation requires `humanWitnessPlan`: a non-empty ordered list of unique witness IDs assigned to `humanAttorneySide`. The API persists the plan and supplies it to the initial graph execution.

Run details retain the finalized `transcript` and add `liveTranscript`, which includes active-witness turns from the latest persisted graph pause. While awaiting a participant, `pendingHumanTurn.context` supplies the action (`opening`, `closing`, `question`, or `objection`), instruction, and—during examination—the witness and phase. Responses also return `humanWitnessPlan`.

## Worker startup

Start an API-service worker that consumes `interactive_trial` before creating
a run. `make worker-all` includes it; `make worker-interactive` runs only this
queue. A queued run has not invoked LangGraph yet, so it cannot produce a
LangSmith trace.

`apps/api-service` owns the public, durable participation API and the RQ
`interactive_trial` queue. `apps/agent-service` remains the internal LangGraph
runtime: workers pass it a stable LangGraph thread id and retain graph state in
its Postgres checkpointer.

Public endpoints:

- `POST /interactive-trial-runs` creates a queued run from `case_file_id` and
  `human_attorney_side` (`defense` is the default).
- `GET /interactive-trial-runs/{runId}` returns lifecycle status, transcript,
  result, a safe error message, and (only while waiting) `pendingHumanTurn`.
- `POST .../turns/{turnId}/upload-authorization` receives `content_type` and
  returns a short-lived PUT URL, required headers, and size limit.
- `POST .../turns/{turnId}/submit` verifies the private object and queues the
  resume worker. Question submissions must also include `is_final` as a
  boolean; this determines whether the attorney has finished that examination
  phase. Audio bytes never pass through FastAPI or Next.js.

Participant recordings use private keys of the form
`interactive-trial-runs/{run-id}/turns/{turn-id}/recording.{extension}`. API
responses intentionally contain neither a recording URL nor R2 credentials.
The worker alone downloads a verified recording and holds its base64 encoding
only in process memory while resuming LangGraph.

Configure `INTERACTIVE_RECORDING_MIME_TYPES`,
`INTERACTIVE_RECORDING_MAX_BYTES`, and `INTERACTIVE_UPLOAD_EXPIRY_SECONDS`.
The R2 bucket must allow the web origin to `PUT`, allow `Content-Type`, and
expose `ETag`; configure retention/lifecycle rules appropriate for participant
recordings, including abandoned and failed runs.
