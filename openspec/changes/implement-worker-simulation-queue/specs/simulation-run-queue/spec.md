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
- **WHEN** the completion consumer receives a successful result message
- **THEN** the system stores the result payload and marks the simulation run `completed`

#### Scenario: Simulation run fails
- **WHEN** enqueueing, worker execution, or completion processing fails
- **THEN** the system records `failed` status with an error message

### Requirement: Execute simulations through worker service
The worker service SHALL consume queued simulation jobs, call the agent-service LangGraph runtime through its public Python contract, and publish completion messages to a separate results queue.

#### Scenario: Worker publishes success
- **WHEN** LangGraph execution returns a trial result
- **THEN** the worker publishes a completion message with `completed` status and the result payload

#### Scenario: Worker publishes failure
- **WHEN** case-file loading or LangGraph execution raises an error
- **THEN** the worker publishes a completion message with `failed` status and an error message

### Requirement: Keep LangGraph queue-agnostic
The agent-service LangGraph runtime MUST NOT depend on Redis, RQ, database writers, or queue callback functions for v1 simulation completion.

#### Scenario: Graph execution finishes
- **WHEN** the worker invokes the agent-service runtime
- **THEN** completion publication is performed by the worker wrapper after the runtime returns or raises
