## 1. Documentation Baseline

- [x] 1.1 Add a minimal root `README.md` describing the courtroom simulator and the primary technologies in the repo
- [x] 1.2 Add a root `AGENTS.md` that defines monorepo boundaries, ownership, and doc sources of truth
- [x] 1.3 Add `apps/web-app/AGENTS.md` with frontend-specific architecture and implementation guidance
- [x] 1.4 Add `apps/web-app/docs/design-system.md` for brand, tokens, layout, and motion guidance

## 2. Web App Architecture Plan

- [x] 2.1 Define the target folder breakdown for shell, playback, transcript, stage, and shared UI concerns in `apps/web-app`
- [x] 2.2 Identify logic currently concentrated in `components/courtroom-app.tsx` and map each concern to its destination module
- [x] 2.3 Decide which current styles remain global tokens and which become component-level styling primitives

## 3. Web App Refactor

- [x] 3.1 Extract playback and manifest-loading logic into focused modules or hooks
- [x] 3.2 Extract transcript, metadata, controls, and timeline panels into reusable UI components
- [x] 3.3 Keep PixiJS stage rendering isolated behind stage-focused client components
- [x] 3.4 Verify the refactor preserves current playback behavior and generated-manifest fallback behavior

## 4. Agent-Service Foundation

- [x] 4.1 Create the initial `apps/agent-service` workspace scaffold when runtime work begins
- [x] 4.2 Define the first service contract between `apps/agent-service` outputs and web-app inputs
- [x] 4.3 Document how generated trial data, verdict outputs, and audio metadata move between workspaces

## 5. Shared Contracts And Follow-up

- [x] 5.1 Decide whether shared schemas need a dedicated shared package or can remain workspace-owned initially
- [x] 5.2 Update OpenSpec artifacts if monorepo tooling or integration boundaries change during implementation
- [x] 5.3 Validate that new docs and refactors keep frontend, backend, and design guidance clearly separated
