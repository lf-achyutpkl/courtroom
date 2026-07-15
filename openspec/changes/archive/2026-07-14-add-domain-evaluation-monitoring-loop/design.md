## Context

The agent-service now returns a stable run envelope and records node telemetry that deterministic validation can inspect before a successful response is returned. That foundation catches broken structure, invalid sequencing, malformed response metadata, and telemetry defects, but it does not answer domain-quality questions such as whether verdict reasoning is supported by cited evidence, whether a witness contradicts known facts without being challenged, or whether a model introduced unsupported legal claims.

The remaining evaluation work spans offline evaluation data, baseline experiments, rule/reference checks, LLM rubric scoring, online monitoring, promptfoo adversarial CI, and human review. These should stay inside `apps/agent-service` because they evaluate simulation/runtime behavior, not frontend playback behavior.

## Goals / Non-Goals

**Goals:**

- Define a versioned evaluation dataset schema and seed 3 courtroom scenarios that cover the initial rule/reference, rubric, and monitoring paths.
- Add a repeatable baseline experiment workflow that can run the seeded cases, persist outputs, and compare evaluator results across graph, prompt, and model versions.
- Add rule/reference evaluators that run after deterministic validation and before subjective LLM rubric scoring.
- Add rubric-based LLM evaluators for domain quality dimensions with stable score schemas, traceable evaluator metadata, and an injectable judge LLM dependency.
- Add online sampling, annotation queue routing, GitHub Issues sync, alert generation, and review cadence documentation keyed by `run_id`.
- Add promptfoo CI tests for the adversarial categories requested by the user.
- Add monitoring validation tests proving trace metadata completeness, node token/latency fields, and queue/alert routing for failed runs.

**Non-Goals:**

- Build a frontend annotation UI in this change.
- Introduce a shared schema package across workspaces before both workspaces need executable validation code.
- Make LLM rubric scores a hard production gate for every run.
- Replace deterministic validation with LLM judges.
- Implement jurisdiction-specific legal advice or real-world legal correctness beyond the simulator's domain constraints and seeded references.

## Decisions

### 1. Keep evaluation code in an agent-service evaluation package

Create an agent-service-owned evaluation area such as `apps/agent-service/src/evaluation/` for dataset schemas, evaluators, experiment runners, monitoring routing, alert policies, and report models. Seed data and promptfoo fixtures should live under agent-service paths such as `apps/agent-service/evals/`.

Why:
- The evaluation target is the Python LangGraph runtime and its trial outputs.
- This preserves the repo boundary: no backend orchestration in the web app and no frontend UI code in the agent service.

Alternative considered:
- Place evaluation logic in repo-level scripts.
- Rejected because evaluator behavior depends on agent-service Pydantic types, runtime config, and trial semantics.

### 2. Version the dataset and separate inputs, references, and expected evaluator signals

Each evaluation case should include:

- `eval_case_id`
- `dataset_version`
- `case_file`
- `reference`
- `tags`
- `expected_signals`

The `case_file` remains the runtime input. The `reference` object captures expected phase coverage, required evidence IDs, forbidden unsupported claims, verdict expectations where applicable, contradiction probes, unsafe-content handling expectations, and evaluator notes.

Why:
- Runtime inputs should not be polluted with evaluator-only ground truth.
- Baseline reports need to detect whether failures come from input changes, reference changes, or runtime changes.

Alternative considered:
- Store expected outputs as full golden transcripts.
- Rejected because the system is generative; strict transcript equality would be brittle and would discourage valid variation.

### 3. Run evaluators in layered order

The experiment workflow should execute:

1. Deterministic validation through the existing service boundary.
2. Rule/reference evaluators against valid outputs.
3. Rubric-based LLM evaluators only when prior layers provide a usable transcript.
4. Monitoring routing for failed, low-scoring, sampled, or escalated runs.

Why:
- Structural failures should not consume LLM judge budget or produce misleading rubric scores.
- Rule/reference checks are cheaper and more deterministic than LLM judges.

Alternative considered:
- Run every evaluator for every run regardless of earlier failures.
- Rejected because it obscures root cause and increases unnecessary cost.

### 4. Treat baseline experiments as immutable report artifacts

Baseline runs should write a machine-readable report containing dataset version, graph version, prompt version, model names, run metadata, evaluator versions, per-case scores, failures, queue decisions, and aggregate metrics. Reports should be timestamped and not overwritten by default.

Why:
- The team needs a regression baseline before changing prompts, graph structure, or evaluator thresholds.
- Immutable reports support weekly review and historical comparison.

Alternative considered:
- Only print results to stdout.
- Rejected because CI and review workflows need stable artifacts.

### 5. Make rubric evaluators structured, domain-specific, and judge-injected

Rubric LLM evaluators should produce typed score outputs for dimensions such as:

- legal grounding against supplied evidence and references
- procedural realism
- role adherence
- contradiction handling
- verdict support
- unsafe-content refusal or containment

Each rubric output should include numeric score, pass/fail threshold, rationale, cited transcript spans or turn IDs where available, evaluator model, evaluator prompt version, and evaluator latency/token metadata.

The default evaluator model is `gpt-4o`. Judge invocation should be decoupled behind a small dependency-injected judge interface so another judge implementation can be plugged in later without changing rubric scoring logic. For this phase, keep the abstraction minimal: the rubric evaluator accepts a judge object or callable that takes the rubric prompt/input and returns the typed rubric result.

Why:
- Free-form judge prose is difficult to trend, alert on, or route to human review.
- Domain-specific dimensions are more actionable than one generic quality score.
- The judge model is an implementation detail of evaluation execution and should not be hard-coded into rubric orchestration.

Alternative considered:
- Use one broad "quality" judge.
- Rejected because it would not isolate legal grounding, role confusion, contradiction, safety, and procedural realism regressions.
- Hard-code OpenAI in the rubric evaluator.
- Rejected because later judge substitution would require invasive rewrites.

### 6. Model monitoring queues as local contracts with GitHub Issues sync

Implement annotation queues and alerts as typed routing records, and add a GitHub Issues sync boundary for records that need human follow-up. Queue records should identify `run_id`, `case_id`, route reason, severity, source evaluator, evidence summary, created timestamp, status, and external tracker fields such as provider, external issue number, external URL, sync status, and last sync timestamp.

Why:
- The project can test routing behavior locally and in CI without requiring external services.
- Human review should not depend only on local files once escalations need ownership and follow-up.
- GitHub is the first chosen external tracker and can be integrated while keeping the local record contract provider-neutral enough for future migration.

Alternative considered:
- Start directly with provider-specific automation rules.
- Rejected because it would make tests brittle and bind core behavior to one external system.

### 7. Add promptfoo as the adversarial CI harness

Use promptfoo for adversarial suites that probe role confusion, contradiction injection, unsupported legal claims, malformed evidence references, and unsafe content prompts. Keep promptfoo tests focused on input/output behavior and route deeper transcript quality checks through the Python evaluators. Expose the suite through a Makefile command and document it in `apps/agent-service/README.md`; do not wire it into automatic CI yet.

Why:
- Promptfoo is purpose-built for prompt/model regression suites and CI-friendly adversarial cases.
- It complements, rather than replaces, structured Python evaluators.
- The team wants to decide later whether promptfoo runs on every pull request, only prompt/runtime changes, or scheduled CI.

Alternative considered:
- Implement every adversarial check as pytest only.
- Rejected because promptfoo gives a better workflow for adversarial prompt cases and future prompt/model matrix testing.

## Risks / Trade-offs

- [LLM rubric evaluators may be noisy] -> Mitigation: keep deterministic and rule/reference checks first, use stable rubric schemas, record evaluator versions, and send borderline or severe failures to human review.
- [Seeded cases may overfit current prompts] -> Mitigation: tag cases by scenario type, include adversarial probes, and expand the dataset as weekly reviews identify blind spots.
- [Promptfoo adds Node-based tooling to a Python workspace] -> Mitigation: keep promptfoo config and invocation isolated from runtime dependencies and document local/CI execution separately.
- [Online alerts can create noisy queues] -> Mitigation: start with explicit thresholds, sampling rates, severity labels, and weekly review calibration.
- [Evaluator reports may expose generated legal content] -> Mitigation: treat eval reports as development artifacts, avoid storing secrets, and keep case data synthetic unless a later policy allows otherwise.

## Migration Plan

1. Add dataset schemas, seed 3 synthetic courtroom scenarios, and schema tests.
2. Add rule/reference evaluators and baseline experiment runner that produce immutable JSON reports.
3. Add rubric evaluator schemas, prompts, default `gpt-4o` evaluator config, injectable judge interface, and tests using mocked judge outputs where possible.
4. Add local monitoring routing records and GitHub Issues sync fields for sampling, annotation queues, escalations, and alerts.
5. Add promptfoo adversarial suite, Makefile command, and README documentation without enabling automatic CI.
6. Add monitoring validation tests for trace metadata, node telemetry token/latency fields, and failed-run queue/alert routing.
7. Update agent-service docs with evaluator contracts, report shape, queue semantics, GitHub Issues sync, alert thresholds, and weekly review cadence.

Rollback is low-risk because the change is additive: disable the baseline or promptfoo CI command while keeping the deterministic runtime gate intact.

## Open Questions

- What are the initial pass thresholds for each rubric dimension before real baseline data exists?
- Which GitHub repository, labels, assignees, and issue template should the external review sync use?
