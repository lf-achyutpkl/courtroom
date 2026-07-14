## Why

The courtroom simulator now produces structured trial runs through a LangGraph-style agent-service, but it lacks a reliable evaluation foundation. We need deterministic validation and traceable run metadata first so prompt or model changes can be measured safely before adding subjective LLM-based quality scoring and production monitoring.

## What Changes

- Add a layered evaluation foundation for `apps/agent-service` with deterministic validation as the first mandatory gate.
- Define the evaluation order as deterministic validation first, then future rule/reference checks, then later LLM-based and online monitoring layers.
- Add run-level and node-level metadata capture so each trial can be traced by case, graph version, prompt version, model, latency, and token usage.
- Extend the agent-service output contract to expose stable run metadata alongside the transcript response.
- Add deterministic validators for state transitions, transcript structure, runtime invariants, and response payloads.
- Add documentation for the evaluation contract, trace fields, and the staged path toward later LangSmith online evaluators and monitoring.

## Capabilities

### New Capabilities
- `courtroom-evaluation-foundation`: Defines the required tracing metadata, deterministic validation rules, and evaluation order for generated courtroom trial runs.

### Modified Capabilities
- None.

## Impact

- Affects `apps/agent-service` runtime types, service entrypoints, graph nodes, and tests.
- Adds agent-service documentation for evaluation and monitoring contracts.
- Establishes the implementation baseline needed before later LangSmith online evaluators, automation rules, and adversarial suites are added.
