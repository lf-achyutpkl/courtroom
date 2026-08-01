## Why

The V2 LangGraph Studio graph creates an OpenAI client but the workspace has no
V2 environment template, dotenv loading, or actionable startup validation.
LangSmith tracing is installed transitively but cannot be configured or enabled
reliably for V2 runs.

## What Changes

- Add a documented, ignored V2 `.env` template for OpenAI and LangSmith.
- Load that local environment file before Studio creates provider clients.
- Validate required OpenAI configuration and validate LangSmith only when
  tracing is enabled.
- Document local setup and a configuration verification command.

## Capabilities

### New Capabilities

- `v2-runtime-environment`: Configure and validate V2 OpenAI and optional
  LangSmith tracing credentials at runtime startup.

### Modified Capabilities

- None.

## Impact

- `apps/agent-service-v2` gains dotenv dependency, startup configuration, and
  local environment documentation.
- No provider secrets are committed; `.env` remains ignored by repository rules.
- Existing graph and domain contracts remain unchanged.
