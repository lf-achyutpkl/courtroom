# Monorepo Contracts

## Workspace Ownership

- `apps/web-app` owns playback, rendering, interaction, and frontend presentation.
- `apps/api-service` owns the FastAPI backend API, normal application persistence, and future job enqueueing.
- `apps/agent-service` owns case simulation runtime concerns, LangGraph flows, retrieval orchestration, evaluation, and generated outputs.
- `apps/worker-service` will own RQ worker processes once Redis-backed background jobs are implemented.
- `infra/db/migrations` owns database schema migrations shared by backend and agent/runtime concerns.

## Initial Integration Contract

The first service boundary is file-oriented and intentionally simple:

- `apps/agent-service` produces trial payloads, verdict metadata, and audio/manifest artifacts.
- `apps/api-service` exposes backend APIs and will enqueue or coordinate runtime work.
- `apps/web-app` consumes structured inputs for playback.

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

Until then, the agent runtime contract source of truth should live in `apps/agent-service/docs/service-contract.md`, while backend API contracts should live with `apps/api-service` or a future shared contract package.
