## MODIFIED Requirements

### Requirement: Human attorney selection
The interactive trial runtime SHALL support a human attorney on the defense or prosecution side, defaulting to defense when the selected side is omitted, and SHALL expose a checkpointable service contract that resumes the same trial thread after each human turn.

#### Scenario: Defense default human side
- **WHEN** an interactive run omits `human_attorney_side`
- **THEN** the graph treats the defense attorney as human

#### Scenario: Durable graph resume
- **WHEN** an API-worker resumes an awaiting-human interactive run
- **THEN** the runtime continues the persisted LangGraph thread rather than starting a new trial graph

### Requirement: Voice turns
The interactive trial runtime SHALL interrupt for each required human-attorney speech turn and SHALL transcribe a worker-supplied, validated audio payload through Deepgram before adding the transcript turn. The runtime SHALL accept that payload through its checkpointed resume contract rather than requiring LangGraph Studio.

#### Scenario: Human opening resumed through the API worker
- **WHEN** an API worker resumes a human opening with validated audio fetched from the participant recording object
- **THEN** Deepgram transcription is appended as the human attorney's opening turn and the graph continues

#### Scenario: Invalid audio payload
- **WHEN** the resumed audio payload is missing, invalid, or cannot be transcribed
- **THEN** the runtime raises a controlled transcription error without appending a fabricated transcript turn
