# AGENTS.md

## Scope

This file applies to `apps/api-service`.

## Purpose

- Keep FastAPI HTTP API code, request/response routing, and backend application boundaries here.
- Own normal product data access patterns, Redis/RQ worker entrypoints, and queue orchestration.
- Do not place LangGraph graph orchestration, prompts, or simulation-agent internals here.
- Do not place frontend UI code here.

## Structure

- `src/api_service/` for the FastAPI package.
- `tests/` for API service tests.
- Database schema migrations live in `infra/db/migrations/`, not in this app workspace.

## Contracts

- Use stable contracts from `docs/` or future shared packages before duplicating request and response shapes.
- Keep the API service as the public backend boundary; the agent service should remain an internal runtime boundary.
