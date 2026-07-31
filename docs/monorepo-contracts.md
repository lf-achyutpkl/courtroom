# Monorepo Contracts

## Workspace Ownership

- `apps/web-app` owns playback, rendering, interaction, and frontend presentation.
- `apps/api-service` owns the FastAPI backend API, normal application persistence, and future job enqueueing.
- `apps/agent-service` owns V1 case simulation runtime concerns, V1 LangGraph flows, retrieval orchestration, evaluation, and generated outputs.
- `apps/agent-service-v2` owns V2 LangGraph runtime concerns, flow state, graph nodes, Studio registrations, prompts, provider wiring, evaluation flows, and generated V2 outputs.
- `packages/courtroom-engine` owns V2 flow-agnostic courtroom intelligence: domain models, compiler validation, fixtures, context boundaries, policies, and deterministic reusable services.
- `apps/worker-service` will own RQ worker processes once Redis-backed background jobs are implemented.
- `infra/db/migrations` owns database schema migrations shared by backend and agent/runtime concerns.

## V1 And V2 Boundary

V1 and V2 runtime code must stay separate:

- V1 graph/runtime code remains in `apps/agent-service`.
- V2 graph/runtime code lives in `apps/agent-service-v2`.
- V2 reusable intelligence logic lives in `packages/courtroom-engine`.
- `packages/courtroom-engine` must not contain LangGraph graphs, Studio config, flow state machines, prompts, LLM/provider clients, or runtime orchestration.
- `apps/agent-service-v2` consumes `packages/courtroom-engine`; the engine must not import from `apps/agent-service-v2`.

V2 flow ownership under `apps/agent-service-v2`:

- `flows/ai_ai/` owns AI-vs-AI orchestration.
- `flows/ai_human/` is reserved for AI-vs-human orchestration.
- `flows/human_human/` is reserved for human-vs-human orchestration.
- `evaluation/` owns V2 graph-level evaluation flows.
- `shared/` owns runtime helpers shared across V2 flows, not domain or engine logic.

## Initial Integration Contract

The first service boundary is file-oriented and intentionally simple:

- `apps/agent-service` produces trial payloads, verdict metadata, and audio/manifest artifacts.
- `apps/agent-service-v2` produces V2 trial payloads, verdict metadata, evaluation outputs, coaching outputs, and playback-ready event artifacts.
- `apps/api-service` exposes backend APIs and will enqueue or coordinate runtime work.
- `apps/web-app` consumes structured inputs for playback.

## V2 AI-vs-AI Runtime Contract

The current supported V2 flow is AI-vs-AI and it is registered in
`apps/agent-service-v2/langgraph.json`.

- `ai-ai-trial` runs the full deterministic structural AI-vs-AI trial flow.
- `ai-ai-evaluation` runs the standalone V2 evaluation graph from prepared trial
  outputs.

Run V2 LangGraph Studio from `apps/agent-service-v2`. Do not register V2 graphs
from `packages/courtroom-engine` or add V2 graph keys to the V1
`apps/agent-service/langgraph.json`.

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

For V2 runtime contracts, use `apps/agent-service-v2/README.md` and future
`apps/agent-service-v2/docs/` documents as the source of truth. Reusable V2
engine contracts belong in `packages/courtroom-engine` docs or OpenSpec
artifacts.
