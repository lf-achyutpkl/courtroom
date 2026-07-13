# Web App Design System

## Purpose

This document is the source of truth for the web app's visual system. Keep agent workflow rules in `AGENTS.md`; keep design rules here.

## Brand Direction

- Tone: cinematic courtroom, editorial, credible, and slightly theatrical
- Interface posture: premium case file meets trial broadcast
- Visual rule: dark judicial base with warm brass accents and evidence-blue support color

## Core Tokens

### Color

- `ink-950`: `#070b16`
- `ink-900`: `#0a1020`
- `ink-800`: `#11192d`
- `panel-700`: `rgba(11, 18, 37, 0.82)`
- `panel-900`: `rgba(6, 10, 23, 0.96)`
- `brass-500`: `#d4a867`
- `brass-300`: `#f2d9ac`
- `evidence-400`: `#8fa5c6`
- `verdict-approve`: `#7dbb9a`
- `verdict-warning`: `#d88963`
- `text-primary`: `#f6efe2`

### Typography

- Display: high-contrast serif for scene headers, rulings, and major case framing
- Sans: readable modern sans for controls, metadata, and transcript UI
- Mono: reserved for timestamps, debug surfaces, and generated IDs

### Spacing And Shape

- Base spacing scale: `4, 8, 12, 16, 24, 32, 48, 64`
- Radius scale: `10, 16, 24`
- Shadows: soft and deep, with emphasis on stage depth instead of card-heavy UI

## Layout Rules

- Use a stage-first layout on desktop with transcript and controls supporting the scene.
- On mobile, stack stage, subtitles, controls, and transcript in that order.
- Keep one strong focal surface per screen. Avoid dashboard-style clutter.

## Motion Rules

- Motion should reinforce speaking turns, scene transitions, and verdict weight.
- Prefer subtle stagger, glow, parallax, and progress motion over generic hover noise.
- Respect `prefers-reduced-motion`.

## Component Guidance

- Build reusable primitives for panels, ribbons, status pills, transcript cards, and transport controls.
- Keep PixiJS stage visuals visually aligned with the DOM shell through shared tokens.
- Subtitle presentation must optimize readability first; do not use oversized comic bubbles for long testimony.

## Recommended Practice

- As of July 2026, the clean split is:
  - `AGENTS.md` for implementation and workspace behavior
  - `docs/design-system.md` for brand and UI system decisions
  - code tokens in CSS or theme files for enforcement
- If design direction changes materially, update this document and the shared tokens together.
