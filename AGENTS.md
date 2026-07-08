# AGENTS.md

## Scope

This file applies to the whole repository.

## Repo Shape

- Treat this repository as a polyglot monorepo.
- `app/web-app` contains the Next.js frontend.
- `agent-service` is reserved for the future Python and LangGraph service.
- Do not place backend orchestration, Python code, or LangGraph graphs inside `app/web-app`.
- Do not place frontend UI code inside `agent-service`.

## Source Of Truth

- Use `openspec/` for change proposals, design docs, and implementation tasks.
- Use this file for repo-wide operating rules.
- Use child `AGENTS.md` files for area-specific implementation rules.
- Keep visual language, brand tokens, and component styling rules in dedicated design-system docs, not in repo-level `AGENTS.md`.

## Working Rules

- Prefer small, composable modules over large orchestration files.
- Preserve clear boundaries between playback UI, simulation logic, content assets, and future agent runtime code.
- Update docs when introducing a new workspace, major folder, or cross-cutting convention.
- If a change affects multiple workspaces, document the boundary and ownership explicitly in OpenSpec artifacts.

## Current Direction

- The web app should move toward a component-based architecture.
- The future `agent-service` should be designed as an independent service contract that can feed the frontend with generated trial data, audio metadata, and verdict outputs.
- Shared schemas and integration contracts should live in dedicated shared documentation or shared packages once they exist.
