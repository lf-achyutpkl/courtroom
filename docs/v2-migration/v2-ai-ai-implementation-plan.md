# V2 AI-vs-AI Intelligence Engine Implementation Plan

## Summary

V2 is an additive intelligence-engine path for AI-vs-AI courtroom simulation. It must not replace the existing POC graph, frontend, API routes, queue workers, or playback contracts.

The first engineering foundation is the redesigned case model and context boundary. Trial state, graph nodes, evaluation, and coaching must be built on top of that foundation rather than driving the case shape.

## Implementation Order

1. Create a new `packages/courtroom-engine` Python package for V2 domain, application, context-boundary, and orchestration code.
2. Define layered case models: authored case template, compiled case package, derived case intelligence, private simulation truth, and runtime trial state.
3. Implement a deterministic case compiler that validates IDs, references, visibility, party ownership, witness knowledge, evidence links, and civil/criminal case structures.
4. Implement role and node-level context boundaries before model-backed graph nodes.
5. Add fail-closed boundary tests proving courtroom actors cannot receive synthetic truth, opposing private strategy, unavailable witness knowledge, hidden contradiction labels, or evaluator-only material.
6. Add a separate LangStudio graph key, `trial-v2-ai-ai`, that points at V2 and leaves `trial` unchanged.
7. Build case intelligence outputs: legal element mapping, evidence graph, timeline graph, witness knowledge boundaries, contradiction candidates, and case-gap records.
8. Build party strategy planning with structured `PartyStrategy`, `CaseTheory`, `StrategicObjective`, `WitnessPlan`, and `EvidencePlan` outputs.
9. Redesign witness examination around objective selection, tactical-action planning, validation, question generation, objection/ruling, witness answer, state update, contradiction detection, and objective-progress assessment.
10. Add structured verdict, evaluation, and coaching after the context boundary and witness loop are reliable.

## Public Interfaces

- New package: `packages/courtroom-engine`.
- New LangStudio graph key: `trial-v2-ai-ai`.
- New V2 graph entrypoint: `apps/agent-service/src/v2/ai_ai_graph.py:graph`.
- Existing `trial` and `examine-witness` graph keys remain unchanged.

## First Vertical Slice

The schemas should support both civil and criminal cases from the start. The first runnable graph should use one compact scenario only, with tests focused on case compilation and context leakage prevention.

## Acceptance Gates

- V2 case templates compile into immutable compiled packages with stable IDs and reference integrity.
- Every model-facing node context is produced through the context boundary service.
- Boundary validation fails closed on forbidden visibility or role-policy violations.
- LangStudio can load `trial-v2-ai-ai` independently from the existing POC graph.
- No frontend or API code is changed.

