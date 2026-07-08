# Monorepo Contracts

## Workspace Ownership

- `app/web-app` owns playback, rendering, interaction, and frontend presentation
- `app/agent-service` owns case simulation runtime concerns, LangGraph flows, retrieval orchestration, and generated outputs

## Initial Integration Contract

The first service boundary is file-oriented and intentionally simple:

- `app/agent-service` produces trial payloads, verdict metadata, and audio/manifest artifacts
- `app/web-app` consumes those outputs as structured inputs for playback

## Expected Output Families

- `case.json`
  - case metadata
  - transcript timeline
  - speaker map
- `verdict.json`
  - verdict outcome
  - supporting rationale summary
  - run metadata
- `manifest.json`
  - playback turn list
  - subtitle chunks
  - audio asset references

## Shared Schema Decision

Shared schemas can remain workspace-owned initially. Introduce a dedicated shared package only after:

- both workspaces modify the same schema regularly, or
- validation logic must run in more than one runtime

Until then, the contract source of truth should live in `app/agent-service/docs/service-contract.md` with the web app consuming the published shape.
