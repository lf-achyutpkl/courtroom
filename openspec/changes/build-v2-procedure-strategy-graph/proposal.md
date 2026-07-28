## Why

The V2 AI-vs-AI graph currently proves case compilation and context-boundary checks, but it does not yet model courtroom procedure, party strategy, or witness examination as structured legal decisions. The next slice should make the engine reason through trial phases like an elite trial lawyer while preserving strict role isolation.

## What Changes

- Add deterministic procedure state, allowed action policies, evidence admission, objection, ruling, and replay-friendly courtroom event models.
- Add reusable party strategy planning models and validators for plaintiff/prosecution and defense, driven by role-safe context and case intelligence.
- Replace the V2 smoke graph internals with a minimum practical AI-vs-AI graph that executes named phases with structured placeholder outputs.
- Add a structured witness examination subgraph that separates objective selection, tactical action planning, question realization, objections/rulings, witness answer validation, and state updates.
- Tighten judge and jury role projections so adjudicators only receive procedurally available trial-record material.

## Capabilities

### New Capabilities

- `v2-trial-orchestration`: Procedure-controlled, role-isolated V2 AI-vs-AI trial orchestration with deterministic strategy and witness-examination scaffolding.

### Modified Capabilities

- None.

## Impact

- Affects `packages/courtroom-engine` domain, policy, context, application, orchestration, graph, fixtures, and tests.
- Keeps `apps/agent-service` graph registration additive through the existing `trial-v2-ai-ai` adapter.
- Does not affect frontend code, FastAPI/RQ workers, or existing V1 `trial` and `examine-witness` graph keys.
