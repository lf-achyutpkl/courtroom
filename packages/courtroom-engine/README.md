# Courtroom Engine

V2 intelligence-engine package for courtroom simulation domain models, case compilation, context boundaries, and LangGraph-compatible orchestration helpers.

## Ownership

- Owns V2 case models, context projection, role policies, compiler validation, and intelligence-engine orchestration primitives.
- Does not own FastAPI routes, RQ workers, persistence APIs, frontend playback UI, or V1 playback contracts.
- Is consumed by `apps/agent-service` for LangStudio/runtime graph execution.

## Current Scope

The initial implementation provides the foundation for AI-vs-AI:

- layered authored and compiled case package models
- civil and criminal case-kind support
- deterministic case compiler checks
- typed context request/envelope models
- fail-closed role-aware context boundary service
- minimal V2 AI-vs-AI graph smoke path

