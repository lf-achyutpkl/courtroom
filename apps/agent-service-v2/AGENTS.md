# AGENTS.md

## Scope

This file applies to `apps/agent-service-v2`.

## Purpose

- Keep V2 LangGraph runtime code, Studio registrations, graph state, graph nodes, prompts, agent-provider wiring, and flow orchestration here.
- Keep reusable courtroom intelligence logic in `packages/courtroom-engine`.
- Keep FastAPI routes and RQ workers in `apps/api-service`.
- Do not place frontend rendering or Next.js code in this workspace.

## Structure

- `src/agent_service_v2/flows/ai_ai/` owns AI-vs-AI graph orchestration.
- `src/agent_service_v2/flows/ai_human/` is reserved for AI-vs-human graph orchestration.
- `src/agent_service_v2/flows/human_human/` is reserved for human-vs-human graph orchestration.
- `src/agent_service_v2/evaluation/` owns graph-level evaluation flows.
- `src/agent_service_v2/shared/` owns shared runtime helpers used by multiple V2 flows.

## Boundaries

- Do not add domain models, compiler logic, context-boundary policy, or deterministic intelligence services here when they are reusable across flows.
- Do not add LangGraph graph builders, Studio config, flow state machines, prompts, LLM/provider clients, or runtime orchestration to `packages/courtroom-engine`.
