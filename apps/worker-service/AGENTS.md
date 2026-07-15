# AGENTS.md

## Scope

This file applies to `apps/worker-service`.

## Purpose

- Keep background worker process code here once RQ and Redis are introduced.
- Workers should consume jobs enqueued by the API service and call agent/runtime packages through explicit contracts.
- Do not place frontend UI code here.
- Do not place public HTTP API route ownership here.

## Status

This workspace is intentionally a placeholder until queue implementation begins.
