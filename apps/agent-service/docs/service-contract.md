# Service Contract

## Goal

Define the first contract between `app/agent-service` outputs and `app/web-app` inputs.

## API Contract

### Run Trial Request

`RunTrialRequest` should provide:

- `case_file`

The caller should not provide orchestration fields such as witness plans, queue state, transcript buffers, summary, or verdict.

### Run Trial Response

`RunTrialResponse` should provide:

- `full_trial_transcript`
- `run`

Internal graph fields like `trial_summary` and `verdict` may still exist during execution, but they are not part of the public API response.

### Run Metadata Envelope

`run` should provide:

- `run_id`
- `case_id`
- `graph_version`
- `prompt_version`
- `model_name`
- `judge_model_name`
- `environment`
- `started_at`
- `completed_at`
- `duration_ms`
- `deterministic_validation_passed`

The public response does not include internal node telemetry. That data remains runtime-only for deterministic validation, tracing, and future monitoring.

## Evaluation Contract

The agent-service validates and evaluates trial runs in layers:

1. Deterministic validation is a hard gate. Structural transcript defects, impossible runtime sequences, or broken response invariants fail the run before a successful response is returned.
2. Rule/reference evaluators score deterministic-valid runs for evidence references, verdict support, contradiction probes, unsupported claims, and required phase coverage.
3. Rubric LLM evaluators score deterministic-valid runs only after prerequisite rule/reference gates pass.
4. Monitoring routes failed, sampled, escalated, or alert-worthy runs to local queue records and optional GitHub Issues sync.

### Evaluation Dataset

The default dataset lives at `evals/domain_evaluation_dataset.json` and is loaded through `src.evaluation.dataset`.

Each active case provides:

- `eval_case_id`
- `dataset_version`
- runtime `case_file`
- evaluator-only `reference`
- `tags`
- `expected_signals`

The runtime `case_file` is the only payload passed to `run_trial`. The `reference` object is evaluator-only ground truth and may include expected phases, required evidence IDs, verdict evidence requirements, required fact phrases, forbidden unsupported claims, contradiction probes, unsafe-content policy notes, and evaluator notes.

### Evaluator Result Schema

Rule/reference evaluators return:

- `evaluator_name`
- `version`
- `passed`
- `severity`
- `findings`
- `related_turn_ids`
- `related_evidence_ids`
- `summary`

Findings include a stable `code`, message, severity, and related turn or evidence IDs when available.

### Rubric Result Schema

Rubric evaluators return typed scores for:

- legal grounding
- procedural realism
- role adherence
- contradiction handling
- verdict support
- unsafe-content handling

Each score includes `score`, `threshold`, `passed`, `rationale`, and cited turn IDs. The rubric result also records evaluator model, prompt version, latency, token usage when available, rationale, and cited turn IDs.

Initial thresholds are:

- legal grounding: `0.75`
- procedural realism: `0.70`
- role adherence: `0.80`
- contradiction handling: `0.75`
- verdict support: `0.80`
- unsafe-content handling: `0.90`

The default judge model is `gpt-4o`. Rubric orchestration must use an injected judge callable or object rather than depending directly on a provider client.

### Baseline Report Shape

Baseline reports are immutable timestamped JSON artifacts under `evals/reports/` by default. A report includes:

- `report_id`
- `dataset_version`
- `graph_version`
- `prompt_version`
- `model_names`
- `evaluator_versions`
- per-case results with run IDs, case IDs, generated output artifact paths, evaluator results, failures, queue decisions, and alert summaries
- aggregate metrics, including deterministic pass rate and overall pass rate
- `created_at`

### Queue Records

Monitoring queue records provide:

- `queue_id`
- `run_id`
- `case_id`
- `route_reason`
- `severity`
- `source_evaluator`
- `evidence_summary`
- `created_at`
- `status`
- `github`

Severity meanings:

- `info`: diagnostic only
- `low`: sampled or minor review item
- `medium`: actionable review but not urgent
- `high`: escalation-worthy evaluator or deterministic failure
- `critical`: urgent failure requiring immediate owner attention

The default sampling policy is explicit opt-in: `sample_rate=0.0` and no tag matches unless configured by the caller.

### GitHub Issues Sync

Queue records support external GitHub tracking fields:

- provider
- issue number
- issue URL
- sync status
- last sync timestamp

GitHub sync is isolated behind a client boundary that accepts a queue record and returns issue metadata. Tests should use a fake client; production configuration must provide the target repository, labels, assignees, and authentication outside the core queue contract.

### Alert Records

Alert records provide:

- `alert_id`
- `run_id` when available
- `severity`
- `trigger_name`
- `source`
- `summary`
- `created_at`
- `routing_target`

Alert rules cover deterministic validation failures, severe evaluator failures, missing trace metadata, and missing node token or latency telemetry. Low-severity evaluator results are recorded without creating high-severity alerts.

## Artifact Output Model

### Case Payload

`case.json` should provide:

- `case_metadata`
- `voice_character_map`
- `audio_script_timeline`

This aligns with the current web app transcript input shape.

### Verdict Payload

`verdict.json` should provide:

- `run_id`
- `outcome`
- `summary`
- `citations`
- `generated_at`

### Playback Manifest

`manifest.json` should provide:

- ordered playback turns
- turn ids and speaker ids
- scene names (`opening`, `direct`, `cross`, `objection`, `ruling`, `closing`, `verdict`)
- cleaned text
- subtitle chunks with start and end timing
- audio asset URLs or relative asset paths

## Data Flow

1. `app/agent-service` generates a trial run.
2. The run emits structured case data and verdict data.
3. Audio generation emits or references timed speech assets.
4. The web app consumes the resulting manifest and displays the playback experience.

## Shared Package Threshold

Do not create a shared schema package yet. Promote these shapes into a shared package only when both workspaces need versioned validation code.
