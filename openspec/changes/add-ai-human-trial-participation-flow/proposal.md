# Add AI-vs-Human Trial Participation Flow

## Why

The interactive trial graph currently accepts human speech only through LangGraph Studio interrupts. Studio is unsuitable as the participant experience: recording and supplying audio is cumbersome, a browser user cannot see the run state, and there is no durable public workflow for resuming a paused trial. We need a small product flow that lets a user launch an AI-vs-human trial, record each attorney response in the browser, and continue the simulation through public APIs.

## What Changes

- Add a dedicated AI-vs-human trial API flow in `apps/api-service`, separate from the existing AI-vs-AI simulation-run endpoints.
- Persist interactive-run state, including the LangGraph thread identity, participant side, current turn/interrupt, status, transcript, and failures.
- Upload recorded browser audio directly to Cloudflare R2 through short-lived, scoped upload authorization; store only the resulting object metadata/key in application records.
- Use Redis/RQ jobs for durable, non-request-path work: starting or resuming the LangGraph run, downloading the recorded object for transcription, and persisting each progressed state.
- Add a basic `apps/web-app` page for starting an AI-vs-human trial, observing transcript/status, recording a response, uploading it, and submitting it to resume the run.
- Define a stable browser/API contract for run creation, status retrieval, pending human-turn details, audio upload, and response submission.

## Capabilities

### New Capabilities

- `interactive-trial-participation-api`: Create, progress, and retrieve public AI-vs-human trial runs with durable state and RQ-backed execution.
- `interactive-trial-audio-upload`: Authorize and record Cloudflare R2-backed participant audio uploads, then attach the immutable audio object to the expected human turn.
- `interactive-trial-participation-ui`: Provide a minimal web flow for a participant to launch, follow, and answer their turns in an AI-vs-human trial.

### Modified Capabilities

- `interactive-trial`: Replace the Studio-only boundary with a reusable interactive execution contract that the API worker can call while retaining the graph's human-interrupt semantics.

## Impact

- Affects `apps/api-service` routes, persistence, RQ jobs/workers, configuration, and database migrations.
- Affects `apps/agent-service` only at its service boundary for API-worker invocation; it remains the owner of trial graph and transcription behavior.
- Affects `apps/web-app` with a new, intentionally basic route and recording/upload client.
- Adds Cloudflare R2 configuration and object-key conventions for user-provided audio; public clients do not receive R2 credentials.
- Documents the cross-service contracts and explicitly keeps existing AI-vs-AI simulation runs unchanged.
