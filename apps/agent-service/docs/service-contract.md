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

The agent-service validates trial runs in layers:

1. Deterministic validation is a hard gate. Structural transcript defects, impossible runtime sequences, or broken response invariants fail the run before a successful response is returned.
2. Future rule-based and reference-based checks may score valid runs once the deterministic gate passes.
3. Future LLM-based evaluators and production monitoring will correlate against `run.run_id`, not against ad hoc logs alone.

## Monitoring Roadmap

This change only establishes the foundation layer:

- Stable run metadata in the public response
- Internal node telemetry for graph execution
- Deterministic validators enforced at the service boundary

Later phases may add:

- LangSmith or similar online trace correlation
- automated evaluator pipelines
- user feedback and annotation workflows keyed by `run_id`

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
- scene names
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
