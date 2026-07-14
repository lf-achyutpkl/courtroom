## ADDED Requirements

### Requirement: Trial runs SHALL use layered evaluation order
The agent-service SHALL treat deterministic validation as the first mandatory evaluation gate for courtroom trial runs before any later rule-based, reference-based, or LLM-based evaluation layers are applied.

#### Scenario: Deterministic validation fails
- **WHEN** a generated trial run violates a structural, schema, or runtime invariant
- **THEN** the agent-service rejects the run as invalid and does not continue to later evaluation layers

#### Scenario: Deterministic validation passes
- **WHEN** a generated trial run satisfies the required structural, schema, and runtime invariants
- **THEN** the run is eligible for later rule-based, reference-based, or LLM-based evaluation layers

### Requirement: Trial responses SHALL include stable run metadata
The agent-service SHALL return a stable run metadata envelope with each successful trial response so downstream systems can correlate outputs with traces, evaluations, and future user feedback.

#### Scenario: Successful trial response
- **WHEN** the service completes a trial run successfully
- **THEN** the response includes a run identifier, case identifier, graph version, prompt version, model identifier, and generation timestamps
- **AND** the response includes deterministic validation status without exposing internal node telemetry records

### Requirement: Runtime telemetry SHALL be captured for major graph nodes
The agent-service SHALL capture structured telemetry for major graph nodes and LLM-backed node executions to support deterministic validation, trace correlation, and future monitoring.

#### Scenario: LLM-backed node executes
- **WHEN** a graph node invokes an LLM-backed structured output
- **THEN** the runtime records the node name, timing, parse status, token usage, and applicable contextual identifiers for that node execution

### Requirement: Deterministic validators SHALL enforce trial structure and contract invariants
The agent-service SHALL validate final run outputs against structural transcript rules, graph progression rules, and public response contract rules before returning the response.

#### Scenario: Transcript structure is invalid
- **WHEN** the generated transcript omits required scenes, uses invalid speaker identifiers, or emits judge-only fields from non-judge turns
- **THEN** deterministic validation fails and the service does not return a successful trial response

#### Scenario: Runtime sequencing is invalid
- **WHEN** node telemetry or final state shows an impossible transition such as a verdict before closings or a witness answer without an active question
- **THEN** deterministic validation fails and the service does not return a successful trial response
