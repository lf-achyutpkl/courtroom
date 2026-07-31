# AGENTS.md

## Scope

This file applies to `packages/courtroom-engine`.

## Purpose

- Keep this package flow agnostic.
- Own reusable courtroom intelligence logic: domain models, compiler validation,
  fixtures, context boundaries, policies, and deterministic services.
- Support AI-vs-AI, AI-vs-human, and human-vs-human flows without depending on
  any one flow.

## Boundaries

- Do not add LangGraph graphs, `StateGraph` builders, Studio configuration,
  flow state machines, prompts, LLM/provider clients, or runtime orchestration
  here.
- Put V2 agentic flow code in `apps/agent-service-v2`.
- Keep `__init__.py` files export-only.
