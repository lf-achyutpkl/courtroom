## ADDED Requirements

### Requirement: Start simulation asynchronously
The API service SHALL expose a public endpoint that starts a simulation from a stored case file without executing LangGraph in the HTTP request path.

#### Scenario: Valid case file is queued
- **WHEN** a client posts a valid `case_file_id` to `POST /start-simulation`
- **THEN** the system creates a simulation run with `pending` status, enqueues a simulation job, and returns the run id with pending status

#### Scenario: Missing case file is rejected
- **WHEN** a client posts a `case_file_id` that does not exist
- **THEN** the system returns `404` and does not enqueue a simulation job

### Requirement: Track simulation run status
The system SHALL persist simulation run lifecycle state in Postgres.

#### Scenario: Simulation run is created
- **WHEN** the API accepts a start-simulation request
- **THEN** the system stores a row with `pending` status and the source case file id

#### Scenario: Simulation run completes
- **WHEN** the dependent persistence job receives a generated result from the prior stage
- **THEN** the system stores the result payload and marks the simulation run `completed`

#### Scenario: Simulation run fails
- **WHEN** enqueueing or any worker stage fails
- **THEN** the system records `failed` status with an error message

### Requirement: Execute simulations through API-owned workers
The API service SHALL own the RQ worker job entrypoints, call the agent-service LangGraph runtime through its public Python contract, and process dependent queue stages inside the same workspace.

#### Scenario: Generation job succeeds
- **WHEN** the LLM worker stage returns a trial result
- **THEN** the system stores the generated result and allows the dependent persistence job to run

#### Scenario: Worker stage fails
- **WHEN** case-file loading or LangGraph execution raises an error
- **THEN** the worker marks the simulation run `failed` with an error message and dependent jobs do not complete the run

### Requirement: Chain stage-specific queue jobs
The system SHALL use dependent jobs across stage-specific queues so later pipeline stages only run after earlier stages succeed.

#### Scenario: Persistence waits for generation
- **WHEN** the API enqueues the simulation pipeline
- **THEN** the DB persistence job depends on the LLM generation job

### Requirement: Keep LangGraph queue-agnostic
The agent-service LangGraph runtime MUST NOT depend on Redis, RQ, database writers, or queue callback functions for v1 simulation completion.

#### Scenario: Graph execution finishes
- **WHEN** the worker invokes the agent-service runtime
- **THEN** queue chaining and persistence are handled by API-service worker layers after the runtime returns or raises
