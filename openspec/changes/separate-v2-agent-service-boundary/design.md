## Boundary

`packages/courtroom-engine` owns reusable courtroom intelligence:

- Domain models, compiler validation, fixtures, context boundaries, policies
- Deterministic planning, examination, deliberation, evaluation, and coaching services

`apps/agent-service-v2` owns V2 agentic runtime behavior:

- LangGraph `StateGraph` builders and Studio `langgraph.json`
- Flow state, graph nodes, graph-level phase sequencing, prompts, and provider wiring
- AI-vs-AI now, with reserved namespaces for AI-vs-human and human-vs-human

## Compatibility

Existing `apps/agent-service` graph files are intentionally not edited. The old
V2 wrapper that imports `courtroom_engine.graph` is no longer the supported V2
entrypoint; new V2 graph execution is hosted in `apps/agent-service-v2`.
