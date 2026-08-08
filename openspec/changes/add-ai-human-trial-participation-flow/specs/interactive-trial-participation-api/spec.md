## ADDED Requirements

### Requirement: Create an interactive trial run
The API service SHALL provide a dedicated endpoint that creates an AI-vs-human trial run from an existing case file and a validated human attorney side, persists a stable LangGraph thread identity, enqueues initial execution through RQ, and returns the run identifier and queued status without waiting for graph completion.

#### Scenario: Valid run creation
- **WHEN** a client creates an interactive trial run for an existing case file with `prosecution` or `defense` as the human side
- **THEN** the API persists a queued run, enqueues its initial job, and returns its identifier and status

#### Scenario: Unknown case file
- **WHEN** a client creates an interactive trial run with a missing case-file identifier
- **THEN** the API rejects the request without creating a run or enqueueing a job

### Requirement: Retrieve interactive trial state
The API service SHALL provide a run-detail endpoint that returns the persisted lifecycle status, human side, transcript/result snapshot, safe failure message when applicable, and the current pending-human-turn descriptor when the run awaits a response.

#### Scenario: Run pauses for the participant
- **WHEN** initial or resumed graph execution reaches a human-attorney interrupt
- **THEN** the detail response reports `awaiting_human` and identifies the expected scene, side, and active turn identifier

#### Scenario: Completed run
- **WHEN** graph execution produces a terminal verdict
- **THEN** the detail response reports `completed` and includes the final snapshot without a pending turn

### Requirement: Resume through durable queued execution
The API service SHALL enqueue human-turn resumes through a dedicated RQ queue and SHALL not invoke or resume the interactive graph in an HTTP request handler. Jobs SHALL use the persisted thread ID and active turn ID, persist the next graph snapshot or interrupt, and be idempotent for retried jobs.

#### Scenario: Submitted recording resumes a paused trial
- **WHEN** a valid recording is submitted for the active pending turn
- **THEN** the API queues a resume job and the worker resumes the matching LangGraph thread from its checkpoint

#### Scenario: Worker retry
- **WHEN** an interactive execution job is retried after partial processing
- **THEN** it does not create another active participant turn or advance the graph twice

### Requirement: Reject stale or invalid human responses
The API service SHALL accept a recording submission only for the run's active pending turn and SHALL reject terminal, failed, mismatched, or already superseded turn identifiers.

#### Scenario: Stale turn submission
- **WHEN** a client submits audio for a prior or non-active turn
- **THEN** the API rejects the submission and leaves the current pending turn unchanged
