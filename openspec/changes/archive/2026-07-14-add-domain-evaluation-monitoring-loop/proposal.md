## Why

Deterministic validation now proves that trial runs are structurally valid, but it does not measure whether the generated courtroom content is legally grounded, internally consistent, or operationally safe. The next evaluation layer needs domain-specific datasets, rubric evaluators, monitoring workflows, adversarial CI, and human review loops that build on the existing run metadata and telemetry foundation.

## What Changes

- Add a reference evaluation dataset schema for courtroom trial runs and seed it with 3 representative courtroom scenarios.
- Add a baseline experiment workflow that runs the seeded dataset through the agent-service and records repeatable evaluator outputs.
- Add rule/reference evaluators for domain invariants such as grounded evidence references, required trial phases, verdict support, contradiction checks, and unsupported legal claim detection.
- Add rubric-based LLM evaluators for qualitative courtroom dimensions after deterministic and rule/reference checks pass, with the judge LLM injected behind a small provider-neutral interface.
- Add online sampling, annotation queues, escalation routing, GitHub Issues sync, and alert definitions keyed by `run_id`.
- Add a promptfoo adversarial CI suite for role confusion, contradiction injection, unsupported legal claims, malformed evidence references, and unsafe content prompts.
- Add monitoring validation tests proving required trace metadata, token/latency fields, and failed-run queue/alert routing.
- Document the weekly review cadence for sampled and escalated runs.

## Capabilities

### New Capabilities

- `domain-evaluation-monitoring`: Defines the dataset, experiment, rule/reference, rubric, online monitoring, adversarial CI, and human review requirements for domain-specific courtroom evaluation.

### Modified Capabilities

- None.

## Impact

- Affects `apps/agent-service` evaluation modules, runtime trace export, test fixtures, and documentation.
- Adds seeded evaluation data and baseline experiment scripts under the agent-service workspace.
- Adds promptfoo configuration and CI-facing adversarial tests for the agent-service.
- Extends `apps/agent-service/docs/service-contract.md` or adjacent evaluation docs with evaluator outputs, queue routing, alert rules, and review cadence.
- May add optional local dependencies for promptfoo execution and structured evaluation reports while keeping frontend UI code out of the agent-service.
