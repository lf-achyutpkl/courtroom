## ADDED Requirements

### Requirement: Create runs with a validated human witness plan

The interactive trial API SHALL accept an ordered `humanWitnessPlan` when creating a run. It SHALL require at least one unique witness ID, verify that every selected witness belongs to the selected human attorney side in the referenced case file, persist the plan with the run, and use it for the initial execution.

#### Scenario: Valid ordered selection
- **WHEN** a defense participant submits unique IDs for defense witnesses in a chosen order
- **THEN** the API creates the run and preserves that order as its human witness plan

#### Scenario: Missing or invalid selection
- **WHEN** the submitted plan is empty, contains duplicate IDs, includes an unknown witness, or includes a witness called by the other side
- **THEN** the API rejects the request and does not enqueue a run

### Requirement: Expose a pause-level live proceeding transcript

The run-detail response SHALL retain `transcript` as the finalized transcript and SHALL additionally return `liveTranscript`, which combines finalized transcript turns with unfinalized active-witness turns from the persisted graph snapshot without duplicating a turn already finalized.

#### Scenario: Witness exchange pauses for participant input
- **WHEN** a graph execution pauses while examining a witness
- **THEN** the run-detail response includes the question, answer, objection, and ruling turns accumulated for that witness in `liveTranscript`

#### Scenario: Witness transcript is published
- **WHEN** active-witness turns have been added to the finalized transcript
- **THEN** `liveTranscript` contains each turn once and `transcript` remains the finalized record

### Requirement: Expose actionable participant-turn context

When a run awaits a human response, the run-detail response SHALL include a typed pending-turn instruction with its action kind, attorney side, and user-facing instruction. A witness-examination instruction SHALL additionally identify the current witness and whether examination is direct or cross.

#### Scenario: Human attorney must ask a question
- **WHEN** the graph pauses for the human attorney to ask a witness question
- **THEN** the response identifies action `question`, the witness ID, name, role, calling side, examination phase, and an instruction to ask that witness a question

#### Scenario: Human attorney may object
- **WHEN** the graph pauses for a human objection decision
- **THEN** the response identifies action `objection` and an instruction that the participant may record an objection or continue without one

### Requirement: Preserve the final-question control

The interactive trial API SHALL require question submissions to include a boolean `is_final`, persist it with the participant turn, and provide it when resuming the checkpointed graph. It SHALL not require this control for objections, openings, or closings.

#### Scenario: Participant submits a witness question

- **WHEN** a participant submits a recorded question with `is_final` set to `true` or `false`
- **THEN** the worker resumes the graph with the same value and the graph can either continue examination or move to the next phase
