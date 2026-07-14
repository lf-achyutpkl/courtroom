## Context

`apps/agent-service` already generates structured courtroom trial transcripts through a LangGraph-style flow, but the runtime only exposes the transcript payload and ad hoc token logging. There is no stable run envelope, no consistent trace metadata, and no deterministic validation layer that can fail fast before subjective evaluation is attempted.

The immediate implementation target is the foundation layer from the broader evaluation plan: traceable run metadata, response contract updates, deterministic validators, and tests. LangSmith online evaluators, production sampling, and adversarial suites remain follow-on phases that should build on the same metadata and validation model.

## Goals / Non-Goals

**Goals:**
- Add a stable run envelope that identifies each trial by run, case, graph version, prompt version, and runtime timestamps.
- Capture structured node telemetry that can be attached to traces and used by deterministic validators.
- Enforce deterministic validation before any later LLM-based evaluation layers are added.
- Expose the new run metadata through the public agent-service contract and document the evaluation contract.
- Add automated tests that prove the deterministic validators catch invalid runtime behavior.

**Non-Goals:**
- Fully implement LangSmith online evaluators, annotation queues, or automation rules.
- Add promptfoo or other adversarial CI suites in this change.
- Score nuanced content quality such as persuasiveness or realism with LLM judges.
- Introduce a shared schema package across workspaces.

## Decisions

### 1. Add a run envelope to the service response

The service will return a `run` metadata object alongside `full_trial_transcript`. The envelope carries stable identifiers and timing/version information regardless of whether tracing backends are enabled.

Why:
- The existing response shape has no durable way to correlate frontend-visible output with backend traces or evaluation records.
- The metadata is cheap to compute locally and does not require LangSmith to be available at runtime.

Alternative considered:
- Keep metadata internal and rely on logs only.
- Rejected because offline evaluation, regression review, and future monitoring need a stable response-level correlation handle.

### 2. Capture node telemetry in code-owned state rather than only through logs

Each node invocation will emit a small telemetry record containing node name, timing, token usage, parse status, and phase-specific context. The trial state will aggregate these records for run-level validation and later export.

Why:
- Deterministic evaluation needs structured runtime facts, not free-form logs.
- This avoids coupling correctness checks to any specific observability backend.

Alternative considered:
- Depend solely on LangSmith traces for node data.
- Rejected because deterministic validation and tests should work locally without external services.

### 3. Make deterministic validation a hard gate at the service boundary

After graph execution completes, the service will validate the final state, transcript, and telemetry before constructing the response. Invalid runs fail immediately instead of returning partial or structurally inconsistent output.

Why:
- Structural/runtime defects are product bugs, not subjective quality issues.
- Failing fast keeps later evaluation layers from producing misleading scores on broken outputs.

Alternative considered:
- Run validators as best-effort warnings.
- Rejected because silent invalid outputs would weaken the evaluation stack and make regressions harder to catch.

### 4. Keep the initial implementation focused on foundation layers

This change will document later monitoring phases but only implement the foundations required for them: metadata hygiene, deterministic validation, and contract updates.

Why:
- The current runtime is small enough that the foundational work can be landed cleanly in one pass.
- Attempting to implement full online monitoring and judge-based evaluation now would add surface area without the supporting metadata discipline.

Alternative considered:
- Add placeholder LangSmith evaluators now.
- Rejected because the runtime still needs stable telemetry and validators first.

## Public Response Contract

Successful trial runs return:

- `full_trial_transcript`: ordered public transcript turns for openings, witness examinations, closings, rulings, and verdict delivery.
- `run.run_id`: stable identifier for the generated run.
- `run.case_id`: case identifier sourced from the input payload.
- `run.graph_version`: runtime graph version label.
- `run.prompt_version`: prompt-template version label.
- `run.model_name`: default model used for most trial nodes.
- `run.judge_model_name`: model used for judge-oriented reasoning nodes.
- `run.environment`: runtime environment label such as `local`.
- `run.started_at` and `run.completed_at`: UTC ISO-8601 timestamps.
- `run.duration_ms`: end-to-end runtime duration in milliseconds.
- `run.deterministic_validation_passed`: hard-gate outcome for the foundation validator layer.

Node telemetry remains internal in this change. The runtime stores it in state for validation, trace correlation, and future monitoring, but does not expose it in the public response until a later contract change explicitly adds it.

## Monitoring Phases

The layered evaluation roadmap is:

1. Deterministic validation blocks structurally invalid runs.
2. Future rule-based or reference-based checks score policy-specific expectations.
3. Future LLM-based evaluators score qualitative dimensions such as realism or persuasiveness.
4. Future online monitoring correlates production traces, user feedback, and evaluator results by `run_id`.

## Risks / Trade-offs

- [Service contract changes may ripple into downstream consumers] -> Mitigation: keep the new metadata additive and document the new response shape in the service contract.
- [Telemetry stored in state increases response payload size] -> Mitigation: keep only the run envelope public and retain node records as internal validation data unless explicitly exported later.
- [Deterministic rules can become too strict and block valid creative outputs] -> Mitigation: limit initial validators to structural and contract invariants, not stylistic judgments.
- [Future tracing backends may use different field names] -> Mitigation: normalize local metadata names now and map them to backend-specific fields later.

## Migration Plan

1. Add runtime metadata types and state fields for run and node telemetry.
2. Instrument graph nodes and LLM invocation helpers to record telemetry consistently.
3. Add deterministic validators and enforce them in `run_trial`.
4. Update agent-service docs and tests to reflect the new response contract and validation rules.
5. Use the new metadata as the required foundation for later LangSmith online evaluation and monitoring work.

## Open Questions

- Should a future API expose node-level telemetry to callers, or remain internal and trace-only?
- Which exact prompt/version identifiers should be treated as release-grade once prompt management becomes more formal?
- When the web app starts calling the service directly, should frontend feedback write back against `run_id` only or against a separate persisted trial record?
