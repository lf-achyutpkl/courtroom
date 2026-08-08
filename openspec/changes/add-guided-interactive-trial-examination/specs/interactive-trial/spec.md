## MODIFIED Requirements

### Requirement: Human attorney selection

The interactive trial runtime SHALL support a human attorney on the defense or prosecution side, accept that attorney's validated ordered witness plan during initial execution, and expose a checkpointable service contract that resumes the same trial thread after each human turn.

#### Scenario: Initial execution receives witness plan
- **WHEN** the API worker starts an interactive run with a validated human witness plan
- **THEN** the runtime initializes the graph with that plan and the human side's queue follows its selected order

#### Scenario: Durable graph resume
- **WHEN** an API worker resumes an awaiting-human interactive run
- **THEN** the runtime continues the persisted LangGraph thread without starting a new trial graph
