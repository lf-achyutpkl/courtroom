## ADDED Requirements

### Requirement: Monorepo reserves an agent-service workspace contract
The repository SHALL document `apps/agent-service` as the planned workspace for Python and LangGraph runtime code.

#### Scenario: Backend runtime work is introduced
- **WHEN** an agent or developer adds the first backend runtime files
- **THEN** the files are placed under `apps/agent-service` instead of being embedded in the web-app workspace

### Requirement: Frontend and agent-service responsibilities stay separate
The repository SHALL document that the future agent-service owns simulation runtime concerns while the web app owns playback and presentation concerns.

#### Scenario: Agent evaluates where new logic belongs
- **WHEN** a new feature includes both generated trial data and frontend playback behavior
- **THEN** the runtime generation logic is assigned to `apps/agent-service` and the rendering or playback UI is assigned to `apps/web-app`
