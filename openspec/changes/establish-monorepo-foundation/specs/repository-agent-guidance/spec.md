## ADDED Requirements

### Requirement: Repository guidance defines workspace boundaries
The repository SHALL provide a repo-level instruction document that defines the monorepo shape, identifies current and planned workspaces, and states where frontend and backend code belong.

#### Scenario: Agent reads repo guidance before editing
- **WHEN** an implementation agent starts work at the repository root
- **THEN** it can identify `apps/web-app` as the frontend workspace and `apps/agent-service` as the reserved Python/LangGraph workspace

### Requirement: Repository guidance separates instruction types
The repository SHALL distinguish implementation guidance from visual-system guidance so repo-level instructions do not become the source of truth for brand and component styling rules.

#### Scenario: Agent needs UI guidance
- **WHEN** an agent needs brand, color, or component-style rules for the web app
- **THEN** the repo guidance directs it to a dedicated design-system document instead of embedding those rules only in the root instruction file
