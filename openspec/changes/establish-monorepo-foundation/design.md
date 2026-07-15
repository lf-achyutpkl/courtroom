## Context

The current repository already contains a working Next.js courtroom prototype under `apps/web-app`, but its runtime flow is concentrated in a small number of broad components, especially `components/courtroom-app.tsx`. The repo does not yet expose monorepo boundaries for a future Python/LangGraph service, and it lacks persistent instructions for coding agents beyond ad hoc app notes. The immediate need is to establish durable documentation and folder ownership so future implementation work can safely split the frontend into composable modules and add `apps/agent-service` without cross-contaminating concerns.

## Goals / Non-Goals

**Goals:**
- Define repository-level and workspace-level operating rules through `AGENTS.md`.
- Separate visual-system guidance from agent-execution guidance by introducing a dedicated design-system document for the web app.
- Establish a target component architecture for the web app that decomposes the current orchestration-heavy client component.
- Reserve a clear workspace contract for a future Python/LangGraph `apps/agent-service` workspace.
- Provide a minimal top-level README that explains the product and technology stack.

**Non-Goals:**
- Fully implement the `apps/agent-service` runtime, LangGraph graph topology, or RAG pipeline.
- Complete the full web-app refactor in this planning change alone.
- Introduce a shared package system before a concrete shared-code need exists.
- Lock in a final brand identity beyond the initial design-system baseline.

## Decisions

### 1. Use layered documentation rather than one oversized `AGENTS.md`

The repo will use repo-level `AGENTS.md` for monorepo boundaries and child `AGENTS.md` files for workspace-specific rules. Design decisions will live in `apps/web-app/docs/design-system.md`.

Why:
- Agent instructions and design-system rules age differently and need different review habits.
- Keeping visual direction outside `AGENTS.md` avoids prompt-style duplication and makes UI rules easier to evolve with code tokens.

Alternative considered:
- Put brand, color, and UI rules directly into `AGENTS.md`.
- Rejected because it mixes behavior guidance with product design and becomes noisy for implementation agents.

### 2. Keep the monorepo contract simple until `apps/agent-service` actually lands

The repo should document `apps/agent-service` as a reserved Python/LangGraph workspace now, but avoid introducing speculative package-sharing infrastructure before there is real integration pressure.

Why:
- The repo only has one implemented workspace today.
- Premature shared tooling would add maintenance cost without proving the interface needs.

Alternative considered:
- Add root-level package managers, shared libraries, or service orchestration immediately.
- Rejected because the current work is boundary-setting, not full-stack bootstrapping.

### 3. Refactor the web app around domain-focused modules

The target frontend shape should separate:
- shell and route composition
- playback controller logic
- transcript and caption UI
- courtroom stage rendering
- shared styled primitives and tokens

Why:
- The current `CourtroomApp` combines manifest loading, playback transport, metadata panels, and transcript rendering.
- This split will make the UI easier to test, restyle, and extend when backend-generated case data arrives.

Alternative considered:
- Keep one high-level orchestration component and only extract small helpers.
- Rejected because it preserves the current coupling between playback state and presentation.

### 4. Treat the design system as a code-backed document, not a one-time brief

The design-system doc defines aesthetic direction, tokens, and component rules, and implementation should gradually mirror those decisions in CSS variables and shared primitives.

Why:
- Durable frontend quality comes from aligning docs and tokens, not from relying on one-time prompts.
- This approach fits the repo's current Tailwind v4 plus CSS-variable setup.

Alternative considered:
- Keep design guidance only in prose notes or AI prompts.
- Rejected because it is not enforceable and drifts quickly.

## Risks / Trade-offs

- [Documentation leads implementation] → Mitigation: keep tasks tightly connected to concrete refactor steps and future folder creation.
- [Monorepo boundaries may evolve once `apps/agent-service` is real] → Mitigation: treat the initial contract as a stable starting point, then revise through new OpenSpec changes when integration details are known.
- [Design-system guidance may outpace the current UI code] → Mitigation: tie new component work to shared tokens and avoid one-off styling additions during the refactor.
- [Too many capability docs could feel heavy for a small repo] → Mitigation: keep each capability narrowly scoped and directly actionable.

## Migration Plan

1. Land baseline repo docs and planning artifacts.
2. Refactor the web app into component and feature boundaries without changing the product premise.
3. Introduce `apps/agent-service` as a new workspace once its service contract and initial runtime are ready.
4. Add shared schemas or packages only when a concrete interface is repeated across workspaces.

## Open Questions

- Will `apps/agent-service` expose data to the web app through files, HTTP APIs, queue jobs, or a hybrid workflow?
- Should shared trial schemas eventually live in a top-level `packages/` workspace or remain service-owned initially?
- Will the web app remain a single route experience or expand into multi-page case management and playback flows?
