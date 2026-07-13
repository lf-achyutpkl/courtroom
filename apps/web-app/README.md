# Courtroom Simulation App

Transcript-driven courtroom playback built with Next.js, PixiJS, and a Kokoro-first speech pipeline.

## What The Two Commands Do

Use `pnpm generate:manifest` when you want the app to run without generating any audio.

- Reads `app/courtroom-transcript.json`
- Reads `app/kokoro-voices.json`
- Creates `public/manifest.json`
- Estimates line durations from text length and voice speed
- Does **not** generate `.wav` files

Use `pnpm generate:kokoro` when you want real speech audio.

- Reads `app/courtroom-transcript.json`
- Reads `app/kokoro-voices.json`
- Generates one `.wav` file per transcript turn into `public/audio/`
- Rebuilds `public/manifest.json` with real audio durations
- This is the command you want for proper synced playback

Short version:

- `generate:manifest` = preview mode, no audio generation
- `generate:kokoro` = real pipeline, generates audio + final manifest

## Recommended Pipeline

### 1. Install app dependencies

```bash
pnpm install
```

### 2. Start with preview mode

```bash
pnpm generate:manifest
pnpm dev
```

Use this when you are working on:

- UI layout
- PixiJS staging and animation
- transcript flow
- subtitle behavior

The app will still play through the courtroom sequence using estimated timings even if no Kokoro audio exists yet.

### 3. Switch to real audio when ready

Install Kokoro requirements first.

```bash
pip install kokoro soundfile numpy
```

You also need `espeak-ng` available on the machine because the Kokoro script depends on it.

Then run:

```bash
pnpm generate:kokoro
pnpm dev
```

This generates:

- `public/audio/*.wav`
- `public/manifest.json`

At runtime, the app prefers the generated audio files automatically. If they are missing, it falls back to the estimated manifest timing.

## Source Files

- `app/courtroom-transcript.json`
  - Source of truth for case metadata, speakers, and transcript lines
- `app/kokoro-voices.json`
  - Maps speakers to Kokoro voice presets
- `scripts/generate-starter-manifest.mjs`
  - Preview manifest generator
- `scripts/generate-kokoro-assets.py`
  - Real Kokoro audio generator
- `public/manifest.json`
  - Playback manifest used by the frontend
- `public/audio/`
  - Generated Kokoro audio output

## Command Reference

```bash
pnpm dev
```

Starts the Next.js app locally.

```bash
pnpm generate:manifest
```

Builds a fallback manifest only. Fast. No Kokoro required.

```bash
pnpm generate:kokoro
```

Builds real audio assets and rewrites the manifest with actual durations.

```bash
pnpm build
```

Creates a production build.

```bash
pnpm lint
```

Runs lint checks.

## Which Command Should You Use?

Use `pnpm generate:manifest` if:

- you are still iterating on UI or animation
- you do not have Kokoro installed yet
- you want the fastest development loop

Use `pnpm generate:kokoro` if:

- you want actual speech output
- you want better sync between captions and playback
- you are testing the final courtroom experience

If you only run one command for the real app flow, use:

```bash
pnpm generate:kokoro
```
