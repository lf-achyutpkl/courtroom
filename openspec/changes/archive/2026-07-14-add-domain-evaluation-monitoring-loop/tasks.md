## 1. Evaluation Dataset

- [x] 1.1 Create `apps/agent-service/src/evaluation/` module structure for dataset schemas, evaluator result models, experiment reports, monitoring records, and utilities
- [x] 1.2 Define Pydantic models for evaluation cases with `eval_case_id`, `dataset_version`, runtime `case_file`, evaluator-only `reference`, `tags`, and `expected_signals`
- [x] 1.3 Add the default seeded dataset file under `apps/agent-service/evals/` with 3 synthetic active courtroom scenarios
- [x] 1.4 Ensure seeded cases cover normal evidence-backed evaluation, contradiction or unsupported-claim evaluation, and adversarial or unsafe-content evaluation
- [x] 1.5 Add tests that load and validate every seeded case against the dataset schema
- [x] 1.6 Add tests that enforce the default 3-scenario dataset count and required coverage tags

## 2. Baseline Experiment Workflow

- [x] 2.1 Implement a baseline experiment runner that loads the default dataset, runs each `case_file` through `run_trial`, and captures deterministic validation failures as per-case results
- [x] 2.2 Define immutable baseline report models with dataset version, graph version, prompt version, model names, evaluator versions, run IDs, case IDs, per-case evaluator results, failures, queue decisions, aggregate metrics, and created timestamp
- [x] 2.3 Write baseline reports to timestamped JSON artifacts without overwriting prior reports by default
- [x] 2.4 Add a documented local command or Makefile target for running the baseline workflow
- [x] 2.5 Add tests for baseline report shape, aggregate metric calculation, and timestamped report naming

## 3. Rule And Reference Evaluators

- [x] 3.1 Implement evaluator result models with evaluator name, version, pass/fail outcome, severity, findings, related turn IDs, related evidence IDs, and summary
- [x] 3.2 Implement rule/reference checks for malformed or unsupported evidence references
- [x] 3.3 Implement required evidence support checks for verdict reasoning and referenced case facts
- [x] 3.4 Implement contradiction probe checks using seeded reference expectations
- [x] 3.5 Implement unsupported legal claim detection using seeded forbidden-claim references
- [x] 3.6 Implement required phase coverage checks for transcript phases expected by each case
- [x] 3.7 Ensure rule/reference evaluators run only after deterministic validation passes
- [x] 3.8 Add unit tests for each rule/reference evaluator failure mode and a passing transcript case

## 4. Rubric-Based LLM Evaluators

- [x] 4.1 Define typed rubric score models for legal grounding, procedural realism, role adherence, contradiction handling, verdict support, and unsafe-content handling
- [x] 4.2 Add rubric evaluator prompt templates, prompt version constants, and default `gpt-4o` judge-model config inside the agent-service evaluation module
- [x] 4.3 Define a minimal judge protocol or callable type that accepts rubric input and returns a typed rubric result
- [x] 4.4 Implement rubric evaluator orchestration that accepts a trial response, case reference, evaluator config, and injected judge dependency, then returns structured score results
- [x] 4.5 Capture evaluator model name, evaluator prompt version, latency, token usage when available, rationale, and transcript references or cited turn IDs when available
- [x] 4.6 Ensure rubric evaluators do not run for deterministic-invalid runs or runs rejected by prerequisite rule/reference gates
- [x] 4.7 Add tests with mocked judge dependencies for valid score parsing, threshold failures, metadata capture, dependency injection, and prerequisite gating

## 5. Monitoring Routing And Alerts

- [x] 5.1 Define monitoring queue record models for sampled, failed, escalated, and alert-worthy runs
- [x] 5.2 Implement sampling policy support for routing a configured percentage or tag-matched set of valid runs to annotation review
- [x] 5.3 Implement queue routing for deterministic failures, high-severity rule/reference failures, rubric threshold failures, and sampled runs
- [x] 5.4 Add GitHub Issues tracking fields to queue records for provider, issue number, issue URL, sync status, and last sync timestamp
- [x] 5.5 Implement a GitHub Issues sync boundary that can create or update issues while remaining testable without network calls
- [x] 5.6 Define structured alert models and alert rules for failed deterministic runs, severe evaluator failures, missing trace metadata, and missing node token/latency telemetry
- [x] 5.7 Ensure alert rules emit severity, trigger name, source, summary, created timestamp, routing target, and `run_id` when available
- [x] 5.8 Add tests for queue routing, alert creation, low-severity alert suppression, failed-run escalation, and GitHub Issues sync metadata

## 6. Promptfoo Adversarial CI Suite

- [x] 6.1 Add promptfoo configuration and fixtures under the agent-service evaluation area or a clearly documented repo path
- [x] 6.2 Add role-confusion adversarial cases
- [x] 6.3 Add contradiction-injection adversarial cases
- [x] 6.4 Add unsupported-legal-claim adversarial cases
- [x] 6.5 Add malformed-evidence-reference adversarial cases
- [x] 6.6 Add unsafe-content prompt adversarial cases
- [x] 6.7 Add a Makefile command for manually running the promptfoo suite that exits non-zero for configured blocking failures
- [x] 6.8 Add lightweight validation that the promptfoo suite contains all required adversarial categories

## 7. Monitoring Validation Tests

- [x] 7.1 Add tests that exported run records include required metadata for `run_id`, `case_id`, graph version, prompt version, model names, environment, timestamps, deterministic validation status, and dataset/evaluator context when applicable
- [x] 7.2 Add tests that node telemetry or exported spans include node name, stage, latency or duration, token fields when available, parse status, and error type when applicable
- [x] 7.3 Add tests that deterministic failures and evaluator threshold failures create expected queue and alert records
- [x] 7.4 Add tests that baseline experiment reports include queue decisions and alert summaries for failed or escalated cases

## 8. Documentation And Review Loop

- [x] 8.1 Update `apps/agent-service/docs/service-contract.md` or add an adjacent evaluation contract doc with dataset schema, evaluator result schema, baseline report shape, queue records, and alert records
- [x] 8.2 Document the baseline experiment workflow and promptfoo adversarial Makefile command in `apps/agent-service/README.md`
- [x] 8.3 Document initial rubric thresholds, severity meanings, sampling policy defaults, default `gpt-4o` judge, and judge dependency injection
- [x] 8.4 Document GitHub Issues sync configuration for sampled and escalated review records
- [x] 8.5 Document the weekly review cadence for sampled runs, escalated runs, severe alerts, rubric failures, unresolved annotation queue items, GitHub Issues, and baseline regression summaries
- [x] 8.6 Document review outcome categories for dataset updates, evaluator threshold changes, prompt/runtime fixes, GitHub Issue follow-up, and no-action decisions

## 9. Verification

- [x] 9.1 Run the agent-service unit test suite for dataset, evaluator, monitoring, and validation changes
- [x] 9.2 Run the baseline experiment workflow against the seeded dataset and confirm a timestamped report is produced
- [x] 9.3 Run the promptfoo adversarial suite command or document any environment dependency that prevents execution
- [x] 9.4 Run `openspec validate add-domain-evaluation-monitoring-loop --strict`
