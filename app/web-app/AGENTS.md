# AGENTS.md

## Scope

This file applies to `app/web-app`.

## Stack

- Next.js 16 App Router
- React 19
- TypeScript
- PixiJS

## Architecture Rules

- Keep route files thin. `app/` should compose features, not hold most of the logic.
- Split the current courtroom experience into focused modules:
  - app shell and page composition
  - playback state and manifest loading
  - transcript and subtitle presentation
  - courtroom stage rendering and animation
  - shared UI primitives and design tokens
- Prefer feature folders and reusable components over one large top-level orchestration component.
- Isolate browser-only PixiJS behavior behind client components and stage-specific modules.

## Design System

- `docs/design-system.md` is the source of truth for brand direction, colors, typography, spacing, motion, and component styling rules.
- Keep durable visual decisions there instead of duplicating them in implementation notes.
- When adding components, use shared tokens first and avoid one-off colors, shadows, and spacing values.

## Implementation Guidance

- Preserve the courtroom tone: judicial, dramatic, legible, and performance-aware.
- Prefer semantic React structure around the PixiJS stage so supporting UI stays testable and accessible.
- Keep transcript data, generated manifests, and playback helpers separate from presentation components.
- Use `public/` only for true static assets or generated playback assets.

## Non-Goals

- Do not turn this workspace into the home for Python services or LangGraph execution.
- Do not encode long-term design rules only inside prompt-style docs when they belong in reusable project docs.
