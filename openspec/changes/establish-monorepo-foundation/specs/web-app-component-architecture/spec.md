## ADDED Requirements

### Requirement: Web app guidance defines component-oriented boundaries
The web app SHALL provide workspace-specific instructions that require thin route files and a component-oriented separation between shell composition, playback logic, transcript UI, and stage rendering.

#### Scenario: Agent plans a frontend change
- **WHEN** an agent modifies the courtroom experience in `app/web-app`
- **THEN** it can determine that orchestration logic and presentation should be split into focused modules instead of expanded inside one large route or app component

### Requirement: Browser-only stage logic remains isolated
The web app SHALL document that PixiJS-specific rendering and browser-only behavior live in stage-focused client modules rather than being spread across unrelated components.

#### Scenario: Agent adds stage behavior
- **WHEN** an agent introduces or updates PixiJS rendering behavior
- **THEN** the work is isolated to browser-safe stage modules and does not force unrelated UI components to become rendering hosts
