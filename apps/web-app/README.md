# Web App

Next.js playback frontend for the courtroom simulator.

## Current State

- Expects a single backend simulation-run payload for transcript metadata and playback manifest data
- Simulation-run list and selection UI are not wired yet
- Optional local bootstrap: set `NEXT_PUBLIC_DEFAULT_SIMULATION_RUN_ID` to fetch one run directly

Backend-owned TTS generation now lives in `apps/api-service`. This workspace does not own audio generation scripts, manifest generation logic, or speaker-to-voice configuration.

## Expected Playback Payload

The playback page now expects a backend response shaped like:

```json
{
  "simulationRunId": "uuid-or-run-id",
  "status": "completed",
  "transcript": {
    "case_metadata": {},
    "voice_character_map": {},
    "audio_script_timeline": []
  },
  "playbackManifest": []
}
```

The frontend currently requests that payload from `/api/simulation-runs/:simulationRunId/playback`.

## Local Development

```bash
pnpm install
pnpm dev
```
