# Courtroom Engine

V2 flow-agnostic intelligence-engine package for courtroom simulation domain
models, case compilation, context boundaries, policies, fixtures, and reusable
deterministic services.

## Ownership

- Owns V2 case models, context projection, role policies, compiler validation,
  and reusable intelligence services.
- Does not own FastAPI routes, RQ workers, persistence APIs, frontend playback UI, or V1 playback contracts.
- Does not own LangGraph graphs, Studio configuration, prompts, LLM/provider
  wiring, or flow-specific runtime state.
- Is consumed by `apps/agent-service-v2` for LangGraph Studio/runtime graph
  execution.

## Current Scope

The initial implementation provides the foundation for AI-vs-AI:

- layered authored and compiled case package models
- civil and criminal case-kind support
- deterministic case compiler checks
- typed context request/envelope models
- fail-closed role-aware context boundary service
- deterministic V2 services for planning, witness examination, deliberation,
  evaluation, and coaching
