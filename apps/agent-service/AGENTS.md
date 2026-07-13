# AGENTS.md

## Scope

This file applies to `app/agent-service`.

## Purpose

- Keep Python runtime code, LangGraph flows, and simulation orchestration here.
- Do not place frontend rendering or Next.js code in this workspace.

## Structure

- `src/agent_service/` for Python packages
- `docs/` for service contracts and runtime notes

## Contracts

- Treat `docs/service-contract.md` as the current output contract for the frontend.
- Keep generated artifact shapes stable or update the contract and downstream consumers together.
