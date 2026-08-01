# Agent Service V2

V2 LangGraph runtime workspace for courtroom simulation flows.

## Responsibilities

- Owns V2 flow orchestration and LangGraph Studio registrations.
- Hosts AI-vs-AI now, with reserved namespaces for AI-vs-human and human-vs-human flows.
- Consumes `packages/courtroom-engine` for reusable domain models, compiler, policies, context boundaries, and deterministic intelligence services.

## Local Development

```bash
uv sync --dev
cp .env.example .env
uv run langgraph dev
```

Set `OPENAI_API_KEY` in `.env` before starting Studio. To trace runs in
LangSmith, set `LANGSMITH_TRACING=true` and provide both `LANGSMITH_API_KEY`
and `LANGSMITH_PROJECT`; `LANGSMITH_ENDPOINT` defaults to the public endpoint
in the template and can be changed for a regional tenant. Environment variables
provided by the shell or deployment secret manager take precedence over `.env`.

To check configuration without making an API request:

```bash
uv run python -c "from agent_service_v2.shared import configure_runtime_environment; configure_runtime_environment(); print('configuration ok')"
```

The package exposes these Studio graph IDs:

- `ai-ai-trial`
- `ai-ai-evaluation`
