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

Internal graph fields like `trial_summary` and `verdict` may still exist during execution, but they are not part of the public API response.

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
