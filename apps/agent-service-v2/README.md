# Agent Service V2

V2 LangGraph runtime workspace for courtroom simulation flows.

## Responsibilities

- Owns V2 flow orchestration and LangGraph Studio registrations.
- Hosts AI-vs-AI now, with reserved namespaces for AI-vs-human and human-vs-human flows.
- Consumes `packages/courtroom-engine` for reusable domain models, compiler, policies, context boundaries, and deterministic intelligence services.

## Local Development

```bash
uv sync --dev
uv run langgraph dev
```

The package exposes these Studio graph IDs:

- `ai-ai-trial`
- `ai-ai-evaluation`
