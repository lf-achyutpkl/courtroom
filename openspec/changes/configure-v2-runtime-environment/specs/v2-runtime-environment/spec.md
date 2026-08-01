## ADDED Requirements

### Requirement: V2 provides a safe environment configuration template

The V2 workspace SHALL provide an ignored `.env.example` that documents the
OpenAI credential and the optional LangSmith tracing variables without secret
values.

#### Scenario: Developer prepares local V2 runtime

- **WHEN** a developer copies the V2 environment template to `.env`
- **THEN** they SHALL see the required `OPENAI_API_KEY` and the optional
  `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, and
  `LANGSMITH_ENDPOINT` variables.

### Requirement: Studio validates runtime credentials

The V2 Studio runtime SHALL load its local environment file without overriding
process variables and SHALL validate required provider configuration before
creating the OpenAI client.

#### Scenario: OpenAI key is absent

- **WHEN** Studio starts without `OPENAI_API_KEY`
- **THEN** it SHALL fail with an actionable configuration error that references
  the V2 environment template.

#### Scenario: LangSmith tracing is enabled incompletely

- **WHEN** `LANGSMITH_TRACING` is true and the LangSmith API key or project is
  absent
- **THEN** Studio SHALL fail with an actionable configuration error.

#### Scenario: Explicit environment wins over local file

- **WHEN** a variable is supplied by the process and also occurs in `.env`
- **THEN** the process value SHALL be retained.
