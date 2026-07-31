## ADDED Requirements

### Requirement: Courtroom engine remains flow agnostic
The `courtroom-engine` package SHALL own reusable courtroom intelligence logic
without depending on LangGraph, Studio registrations, prompts, provider clients,
or flow-specific runtime orchestration.

#### Scenario: Engine has no graph runtime surface
- **WHEN** the engine package is inspected
- **THEN** it does not contain LangGraph graph builders, graph entrypoints,
  Studio config, or LangGraph package dependencies

### Requirement: Agent service V2 owns flow orchestration
The `agent-service-v2` workspace SHALL own V2 LangGraph graph state, graph nodes,
graph builders, Studio registration, and flow-specific runtime sequencing.

#### Scenario: AI-vs-AI graphs run from agent service V2
- **WHEN** LangGraph Studio loads `apps/agent-service-v2/langgraph.json`
- **THEN** the AI-vs-AI trial, witness-loop, and evaluation graph IDs import from
  `agent_service_v2`

### Requirement: V2 runtime supports future flow families
The `agent-service-v2` workspace SHALL provide separate namespaces for AI-vs-AI,
AI-vs-human, and human-vs-human flows so future graph implementations do not
share ambiguous ownership.

#### Scenario: Future flow namespaces are reserved
- **WHEN** a new V2 flow is added
- **THEN** its graph orchestration is placed under the matching flow namespace in
  `agent-service-v2` rather than in `courtroom-engine`
