## ADDED Requirements

### Requirement: Evaluation dataset schema

The agent-service SHALL define a versioned evaluation dataset schema for domain-specific courtroom evaluation cases.

#### Scenario: Dataset case contains runtime and reference fields

- **WHEN** an evaluation case is loaded
- **THEN** it MUST include an `eval_case_id`, `dataset_version`, runtime `case_file`, evaluator-only `reference`, `tags`, and `expected_signals`

#### Scenario: Dataset schema validates seeded cases

- **WHEN** the seeded evaluation dataset is checked
- **THEN** every case MUST validate against the dataset schema before experiments run

### Requirement: Seeded domain evaluation scenarios

The agent-service SHALL include 3 seeded synthetic courtroom evaluation scenarios covering the initial evaluation and monitoring paths.

#### Scenario: Seeded case coverage is checked

- **WHEN** dataset coverage tests run
- **THEN** the seeded cases MUST include coverage for normal evidence-backed evaluation, contradiction or unsupported-claim evaluation, and adversarial or unsafe-content evaluation

#### Scenario: Seeded case count is checked

- **WHEN** the default domain evaluation dataset is loaded
- **THEN** it MUST contain exactly 3 active scenarios unless the dataset version is explicitly changed

### Requirement: Baseline experiment workflow

The agent-service SHALL provide a baseline experiment workflow that runs the seeded dataset through the trial service and writes repeatable evaluation reports.

#### Scenario: Baseline report records runtime versions

- **WHEN** a baseline experiment completes
- **THEN** the report MUST include dataset version, graph version, prompt version, runtime model names, evaluator versions, run IDs, case IDs, per-case evaluator results, failures, queue routing decisions, aggregate metrics, and report creation timestamp

#### Scenario: Baseline report is immutable by default

- **WHEN** a baseline experiment writes a report
- **THEN** it MUST create a new timestamped report artifact by default rather than overwriting the previous baseline report

### Requirement: Rule and reference evaluators

The agent-service SHALL evaluate deterministic-valid trial outputs with rule/reference evaluators before any LLM rubric evaluator is invoked.

#### Scenario: Rule evaluators run after deterministic validation

- **WHEN** a trial run fails deterministic validation
- **THEN** rule/reference and LLM rubric evaluators MUST NOT treat that run as a valid quality-scoring candidate

#### Scenario: Reference checks detect domain defects

- **WHEN** a deterministic-valid transcript contains unsupported evidence references, missing required evidence support, unresolved contradiction probes, unsupported legal claims, missing required trial phases, or verdict reasoning inconsistent with the case reference
- **THEN** the rule/reference evaluator results MUST record the failing check, severity, related turn IDs or evidence IDs when available, and pass/fail outcome

### Requirement: Rubric-based LLM evaluators

The agent-service SHALL provide structured rubric-based LLM evaluators for qualitative courtroom quality dimensions through an injectable judge LLM dependency.

#### Scenario: Rubric evaluator returns typed scores

- **WHEN** a rubric evaluator scores a valid trial transcript
- **THEN** it MUST return typed scores for legal grounding, procedural realism, role adherence, contradiction handling, verdict support, and unsafe-content handling with pass/fail thresholds and rationale

#### Scenario: Rubric evaluator records evaluator metadata

- **WHEN** a rubric evaluator produces a result
- **THEN** the result MUST include evaluator model, evaluator prompt version, latency, token usage when available, and transcript references or cited turn IDs when available

#### Scenario: Rubric evaluator uses default judge model

- **WHEN** no evaluator model override is provided
- **THEN** rubric evaluators MUST use `gpt-4o` as the default LLM judge model

#### Scenario: Rubric evaluator uses injected judge dependency

- **WHEN** a rubric evaluator invokes an LLM judge
- **THEN** it MUST use an injected judge object or callable rather than directly depending on a provider-specific client

### Requirement: Online sampling and annotation queues

The agent-service SHALL define local monitoring routing records for sampled, failed, escalated, and alert-worthy trial runs.

#### Scenario: Run is routed to annotation queue

- **WHEN** a run is selected by sampling policy or fails a configured evaluator threshold
- **THEN** the monitoring layer MUST create a queue record containing `run_id`, `case_id`, route reason, severity, source evaluator, evidence summary, created timestamp, and status

#### Scenario: Queue record supports external tracking

- **WHEN** a queue record requires human follow-up
- **THEN** the record MUST support GitHub Issues tracking fields for provider, issue number, issue URL, sync status, and last sync timestamp

#### Scenario: Queue record syncs to GitHub Issues

- **WHEN** GitHub sync is enabled for a human-review queue record
- **THEN** the monitoring layer MUST create or update a GitHub Issue and store the issue number and URL on the queue record

#### Scenario: Failed run is escalated

- **WHEN** deterministic validation fails or a high-severity evaluator result is produced
- **THEN** the monitoring layer MUST route the run to an escalation queue and produce an alert record

### Requirement: Alert policy

The agent-service SHALL define alert rules for failed deterministic runs, severe evaluator failures, missing trace metadata, and missing node token/latency telemetry.

#### Scenario: Alert rule emits structured alert

- **WHEN** an alert rule is triggered
- **THEN** the system MUST emit a structured alert containing `run_id` when available, severity, trigger name, source, summary, created timestamp, and routing target

#### Scenario: Alert policy suppresses non-actionable noise

- **WHEN** a low-severity evaluator issue does not meet an alert threshold
- **THEN** the monitoring layer MUST record the evaluator result without creating a high-severity alert

### Requirement: Promptfoo adversarial CI suite

The repository SHALL include a promptfoo adversarial CI suite for courtroom-specific prompt and model regression probes.

#### Scenario: Adversarial suite covers required categories

- **WHEN** the promptfoo suite is inspected or run
- **THEN** it MUST include tests for role confusion, contradiction injection, unsupported legal claims, malformed evidence references, and unsafe content prompts

#### Scenario: Adversarial suite is CI-addressable

- **WHEN** CI or a developer invokes the documented adversarial command
- **THEN** promptfoo MUST run the configured suite and return a non-zero exit code for configured blocking failures

#### Scenario: Adversarial suite is manually invoked

- **WHEN** the promptfoo suite is added
- **THEN** it MUST be exposed through a Makefile command and documented in `apps/agent-service/README.md` without being automatically wired to every pull request

### Requirement: Monitoring validation tests

The agent-service SHALL include tests that validate monitoring and traceability contracts.

#### Scenario: Required trace metadata is validated

- **WHEN** monitoring validation tests inspect a completed run
- **THEN** traces or exported run records MUST include required metadata for `run_id`, `case_id`, graph version, prompt version, model names, environment, timestamps, deterministic validation status, and dataset/evaluator context when applicable

#### Scenario: Node spans include token and latency fields

- **WHEN** monitoring validation tests inspect node telemetry or exported node spans
- **THEN** each node span MUST include node name, stage, duration or latency field, token fields when available, parse status, and error type when applicable

#### Scenario: Failed runs route correctly

- **WHEN** a run fails deterministic validation or a configured evaluator threshold in tests
- **THEN** the monitoring layer MUST create the expected queue and alert records

### Requirement: Human review cadence

The agent-service documentation SHALL define a weekly review cadence for sampled and escalated evaluation runs.

#### Scenario: Weekly review inputs are documented

- **WHEN** a reviewer follows the documented weekly review process
- **THEN** the process MUST identify sampled runs, escalated runs, severe alerts, rubric failures, unresolved annotation queue items, and baseline regression summaries as review inputs

#### Scenario: Review outcomes are recorded

- **WHEN** a weekly review decision is made
- **THEN** the process MUST record whether the outcome requires dataset updates, evaluator threshold changes, prompt/runtime fixes, GitHub Issue follow-up, or no action
