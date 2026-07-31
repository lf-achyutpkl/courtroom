## Why

`packages/courtroom-engine` should be reusable across AI-vs-AI, AI-vs-human,
and human-vs-human modes. Hosting LangGraph graphs and Studio configuration in
that package makes it flow-specific and weakens the service boundary.

## What Changes

- Move V2 LangGraph graph state, nodes, graph builders, and Studio registrations
  into a new `apps/agent-service-v2` workspace.
- Keep deterministic reusable intelligence services in `packages/courtroom-engine`.
- Remove engine-level LangGraph dependencies and graph entrypoints.
- Add boundary tests so graph runtime code does not drift back into the engine.

## Capabilities

### New Capabilities

- `v2-agent-service-boundary`: Flow-agnostic engine ownership with V2
  LangGraph runtime ownership in `apps/agent-service-v2`.

### Modified Capabilities

- None.

## Impact

- Adds `apps/agent-service-v2` as the supported V2 LangGraph runtime workspace.
- Leaves existing `apps/agent-service` graph files untouched.
- Deprecates the old `courtroom_engine.graph` entrypoint by removing it.
