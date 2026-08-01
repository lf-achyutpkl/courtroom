## Context

V2 compiles a hard-coded `build_reference_case()` during initialization, and its Studio export builds a graph without the executor required by every live-prompt node. The engine already owns flow-agnostic authored templates and fixtures; V2 owns runtime state and provider wiring.

## Goals / Non-Goals

**Goals:**

- Provide a realistic, evenly contestable criminal fixture with clear coaching pivots.
- Permit a caller to select an `AuthoredCaseTemplate` through V2 graph state.
- Make the Studio graph create a configured OpenAI Responses executor.

**Non-Goals:**

- Adapt the legacy `CaseFile` JSON model or add API/UI case selection.
- Guarantee verdict percentages or randomize an outcome.
- Move provider or graph code into the courtroom engine.

## Decisions

- Add an optional `case_template` field to `V2AiAiState`. Initialization compiles this value, falling back to `build_reference_case()` for compatibility. This avoids a new configuration channel and makes each invocation self-contained.
- Put the prototype-theft fixture in `courtroom_engine.fixtures`, alongside the existing reference fixtures. It uses public, party-private, witness-private, evaluator-only, and coach-only material through the existing domain contract.
- Construct `OpenAIResponsesPromptExecutor(OpenAI())` in Studio. Missing credentials remain an OpenAI runtime configuration error rather than silently falling back to deterministic behavior.
- Use a disputed badge/access record and potentially offset clocks as the pivotal conflict. A party must authenticate or impeach this evidence effectively; no hidden fact declares either party correct.

## Risks / Trade-offs

- [A caller supplies an invalid template] → compile it during initialization and surface the engine validation error before any prompt call.
- [Studio import requires OpenAI configuration] → retain lazy API access; only invocation requires valid credentials.
- [Fixture evidence is accidentally decisive] → tests assert both sides have material evidence and an expected contradiction, while coaching evaluates advocacy quality rather than forcing a result.

## Migration Plan

Existing invocations omit `case_template` and continue to run the reference fixture. Roll back by omitting the new fixture and field; no persisted schema or API migration is required.

## Open Questions

None.
