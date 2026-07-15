# AGENTS.md

## Scope

This file applies to `apps/agent-service`.

## Purpose

- Keep Python runtime code, LangGraph flows, prompts, evaluations, and simulation orchestration here.
- Keep FastAPI route ownership in `apps/api-service`.
- Keep future RQ worker process ownership in `apps/worker-service`.
- Do not place frontend rendering or Next.js code in this workspace.

## Structure

- `src/agent_service/` for Python packages
- `docs/` for agent runtime contracts and runtime notes

## Contracts

- Treat `docs/service-contract.md` as the current output contract for the frontend.
- Keep generated artifact shapes stable or update the contract and downstream consumers together.
