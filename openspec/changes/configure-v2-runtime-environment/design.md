## Context

V2 currently constructs `OpenAI()` during Studio module import. The OpenAI SDK
reads process variables, but neither it nor Python reads a workspace `.env`
file by default. LangSmith tracing is configured through process variables and
is optional for local development.

## Goals / Non-Goals

**Goals:**

- Provide one discoverable, V2-owned configuration contract.
- Fail fast with a safe, actionable error when OpenAI credentials are absent.
- Enable LangSmith tracing only when explicitly requested and completely
  configured.

**Non-Goals:**

- Make an API request during startup validation.
- Persist, print, or commit credential values.
- Change graph topology or provider request behavior.

## Decisions

- Use `python-dotenv` to load `apps/agent-service-v2/.env` without overwriting
  explicitly supplied process variables.
- Use a small shared standard-library configuration module instead of adding a
  settings framework.
- Require `OPENAI_API_KEY` for the Studio graph. Treat LangSmith as disabled
  unless `LANGSMITH_TRACING` is true; require its API key and project then.
- Keep the official current LangSmith variables (`LANGSMITH_*`) in the template;
  do not rely on legacy `LANGCHAIN_*` aliases.

## Risks / Trade-offs

- Studio imports now fail earlier without `OPENAI_API_KEY`; this replaces the
  SDK's less contextual error with a workspace-specific message.
- `.env` loading is intentionally local-development convenience. Production
  deployments should supply the same variables through their secret manager.

## Migration Plan

Copy `.env.example` to `.env`, supply the required OpenAI key, and optionally
enable LangSmith tracing. Existing deployments using environment variables
continue to work because dotenv does not override them.
