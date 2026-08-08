# Add Guided Interactive Trial Examination

## Why

The current AI-vs-human trial page becomes ambiguous once witness examination starts. A participant can be asked to record an unspecified response while the UI neither identifies the witness nor states whether the response is a question, an objection, an opening, or a closing. The public run response also exposes only the finalized transcript, hiding question, answer, objection, and ruling turns that have accumulated for the active witness.

In addition, a human attorney's witness plan is required by the interactive graph but cannot be provided when a browser user starts a run. A missing plan can leave the human side with no valid witness queue.

## What Changes

- Add a required, ordered witness-selection step before starting an AI-vs-human trial. The participant selects witnesses assigned to their side; the chosen IDs become the human witness plan for the run.
- Extend the interactive-run create and read contracts to retain the selected plan and provide enough active-turn context for the browser to state the required action and identify the witness on the stand.
- Publish a pause-level live transcript in run responses by combining the finalized trial transcript with the active witness transcript stored in the persisted graph snapshot.
- Replace the generic recorder prompt with action-specific guidance and controls for questions, objections, openings, and closings.
- Keep the existing polling model. The UI will refresh at graph pause boundaries; this change does not introduce streaming, WebSockets, or change graph execution semantics.

## Impact

- Affects `apps/web-app` trial setup, live proceeding presentation, typed browser API client, and accessibility announcements.
- Affects `apps/api-service` interactive-run request/response schemas, persisted run data, and read-model projection of the existing state snapshot.
- Affects `apps/agent-service` only at its public interactive execution contract so the initial invocation receives the selected witness plan. The LangGraph witness loop and trial logic remain unchanged.
- Adds delta requirements for `interactive-trial-participation-api`, `interactive-trial-participation-ui`, and the interactive runtime contract.
