## Context

The existing interactive participation flow deliberately provides a minimal browser recorder. It returns the completed `full_trial_transcript` and a pending turn with only an ID, scene, and attorney side. During witness examination, the graph instead appends turns to `current_witness_transcript` until the witness subgraph publishes them. The browser therefore loses the context needed to take a meaningful next action.

The graph also requires `human_witness_plan` when a human side is selected, while the public create-run request has no way to collect, persist, or pass that plan.

## Goals / Non-Goals

**Goals:**

- Make trial setup collect an ordered, valid witness plan for the participant's side.
- Give each pending browser turn a stable action type and enough context to tell the participant exactly what to say.
- Show finalized and active-witness transcript turns after each persisted graph pause.
- Preserve the existing RQ, checkpoint, polling, recording, and audio-upload architecture.

**Non-Goals:**

- Stream token-, audio-, or node-level events while a worker invocation is still running.
- Change question generation, objection decisions, judicial rulings, witness ordering rules, or the LangGraph loop.
- Add a rich text editor, playback timeline, authentication, or multi-participant collaboration.

## Decisions

### 1. Capture the human-side witness queue before creating a run

The setup screen will load witnesses from the selected case file, filter them to the selected human attorney side, and require an ordered selection of at least one witness. The request carries `human_witness_plan` as witness IDs in presentation order. The API validates that all IDs are unique and belong to that side, persists the JSON array on the run, and passes it to the initial interactive execution.

The opponent's strategy-generated plan remains graph-owned. The human plan is immutable after run creation so the checkpointed execution is deterministic. A selected case with no eligible witnesses displays a blocked setup state with a link or instruction to assign witnesses in the case editor.

### 2. Project pause-level live transcript from the persisted graph snapshot

Each worker invocation already persists `state_snapshot` when it reaches an interrupt or terminal state. The API read model will project a `live_transcript` from `full_trial_transcript` followed by `current_witness_transcript`, excluding an active turn that has already appeared in the finalized portion. It will use deterministic turn content/metadata comparison until a persistent turn ID is available.

`transcript` remains the finalized record for compatibility. `liveTranscript` is the browser-facing progression view and may include unfinalized active-witness turns. This permits a UI refresh after every participant decision without adding a streaming transport.

### 3. Use a typed participant instruction instead of a generic scene

The normalized pending-turn response will include an action kind (`opening`, `closing`, `question`, or `objection`), attorney side, and a contextual instruction. For witness turns it also includes the current witness's ID, name, persona, calling side, and examination phase (`direct` or `cross`). The API derives this from the persisted state snapshot and normalized graph interrupt; the browser never interprets raw LangGraph state itself.

The UI maps action kind to controls:

- `question`: record and submit a question for the named witness; no no-objection control.
- `objection`: show the preceding question/answer in the live record and offer Record objection or No objection — continue.
- `opening` and `closing`: record and submit the named statement.

### 4. Keep polling and persist only at pause boundaries

The browser continues bounded polling while a run is queued, running, or awaiting a response. It immediately refreshes after a successful submission. A worker's state becomes visible when `store_progress` completes at an interrupt or terminal state. This intentionally does not promise that a user can observe individual nodes during one uninterrupted worker run.

## Data Flow

```text
setup: case + side + ordered human witness IDs
                  │
                  ▼
POST /interactive-trial-runs ──► persisted run ──► RQ initial invocation
                  │                                      │
                  │                                      ▼
GET run ◄── response projection ◄── state snapshot at a graph pause
  │          - transcript (finalized)
  │          - liveTranscript (finalized + active witness)
  │          - pendingHumanTurn (typed instruction + witness)
  ▼
action-specific recorder UI ──► submit ──► RQ resume
```

## Risks / Trade-offs

- Snapshot projection can temporarily show turns that are not in the final record. The UI labels the panel as a live proceeding, and the finalized `transcript` remains available for durable results.
- A content-based deduplication rule is less robust than turn IDs. It is safe for the current append-only model; a future graph schema can add stable turn IDs without changing the response shape.
- Requiring a human witness plan prevents ambiguous starts, but cases without witnesses for the chosen side cannot start until the case is corrected. This is preferable to a graph failure after queue construction.

## Migration Plan

1. Add run persistence and public-schema fields with backward-compatible defaults for existing rows.
2. Update agent-service invocation, API projection, and tests before deploying the UI so older clients continue to read `transcript`.
3. Deploy the guided setup and action card once the read contract is available.
4. Roll back by hiding the new UI flow; existing persisted runs retain their snapshots and remain readable.
