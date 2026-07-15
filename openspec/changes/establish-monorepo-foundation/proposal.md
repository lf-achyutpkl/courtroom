## Why

The repository has an early Next.js courtroom prototype, but it does not yet have a clear monorepo contract, repo-level agent guidance, or a component architecture that can scale into a web client plus a Python `apps/agent-service` workspace. This work is needed now so implementation can proceed against stable repo rules instead of mixing UI, runtime orchestration, and future backend concerns into one code path.

## What Changes

- Define the repository as a polyglot monorepo with a clear separation between the existing `apps/web-app` frontend and a planned `apps/agent-service` Python/LangGraph workspace.
- Add repository-level and app-level `AGENTS.md` files that tell coding agents where code belongs, how to work in each area, and which docs are the source of truth.
- Establish a dedicated web design-system document for brand direction, tokens, layout principles, motion, and component rules rather than embedding visual guidance inside `AGENTS.md`.
- Plan the refactor of the Next.js courtroom app from orchestration-heavy pages/components into a proper component-based structure with reusable UI, playback, and stage modules.
- Define the initial monorepo documentation baseline with a simple top-level `README.md`.

## Capabilities

### New Capabilities
- `repository-agent-guidance`: Repository-level conventions for monorepo boundaries, documentation ownership, and agent operating rules.
- `web-app-component-architecture`: A component-oriented frontend structure for the courtroom app, including separation of scene rendering, playback state, transcript UI, and shell layout.
- `web-app-design-system`: A dedicated design-system source of truth for brand direction, tokens, motion, and frontend implementation rules.
- `agent-service-workspace-foundation`: Initial monorepo expectations for the future Python/LangGraph service so it can be added without leaking backend concerns into the web app.

### Modified Capabilities
- None.

## Impact

- Affects repository documentation and planning artifacts at the repo root and `apps/web-app`.
- Defines future folder ownership for `apps/web-app` and `apps/agent-service`.
- Guides later refactors in Next.js 16 / React 19 / PixiJS code and the future Python LangGraph service.
- Adds no runtime dependency immediately, but shapes subsequent frontend and backend implementation work.
