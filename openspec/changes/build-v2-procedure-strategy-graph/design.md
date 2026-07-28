## Context

V2 currently has a typed case package, deterministic case intelligence, actor-facing DTO projections, and a `trial-v2-ai-ai` smoke graph. It does not yet represent procedure, strategy, events, or examination as structured state transitions. The north-star product needs those layers before any model-backed courtroom dialogue is useful.

## Goals / Non-Goals

**Goals:**

- Add deterministic procedure and event foundations for replayable trial execution.
- Add role-isolated strategy planning scaffolding for both sides.
- Expand `trial-v2-ai-ai` into a runnable structural AI-vs-AI graph with opening, witness, closing, deliberation, and evaluation phase outputs.
- Redesign witness examination around objectives, tactical actions, validation, rulings, witness answers, and state updates.

**Non-Goals:**

- No frontend, FastAPI, RQ, or worker changes.
- No changes to V1 `trial` or `examine-witness`.
- No live LLM calls or realistic transcript generation in this slice.
- No AI-vs-human interrupts, human-vs-human mode, production learning loop, or multi-jurisdiction implementation.

## Decisions

- Keep this slice deterministic with model-port-ready DTOs. This proves boundaries, graph shape, and validation before adding LLM variability.
- Put canonical models in `domain`, pure services in `application`, policies in `policies`, and LangGraph builders in `orchestration`.
- Treat the procedure controller as the source of allowed phases/actions. Context assembly will read policy output instead of embedding ad hoc allowed-action lists.
- Store strategy privately by side. The evaluator may inspect both strategies later, but lawyer contexts and question-generation briefs must not include opponent private strategy.
- Keep root graph state reference-oriented and compact. Phase outputs and event summaries are stored instead of copying the full case package into every node-specific object.

## Risks / Trade-offs

- Deterministic placeholder output will not yet feel like a real trial transcript -> mitigate by preserving typed model ports and execution briefs for later model-backed nodes.
- More domain models increase surface area before full behavior exists -> mitigate with focused tests and compatibility exports only for stable public types.
- Judge and jury context rules are initially simple -> mitigate by making admitted-record projection explicit and fail-closed.
- Structural graph may underrepresent advanced procedure -> mitigate by modeling phase/action/ruling records now and extending policies later.
