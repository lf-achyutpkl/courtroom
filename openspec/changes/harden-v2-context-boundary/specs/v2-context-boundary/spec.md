## ADDED Requirements

### Requirement: V2 model-backed nodes receive DTO-only contexts

V2 model-backed nodes SHALL receive actor-facing context DTOs rather than canonical case package models.

#### Scenario: Context projection excludes canonical package internals

- **WHEN** a context is assembled for a trial actor
- **THEN** the returned model-facing context contains projected fact, evidence, witness-knowledge, actor, procedure, metadata, and audit DTOs
- **AND** it does not expose `CompiledCasePackage` or `PrivateSimulationTruth`

### Requirement: V2 context assembly is auditable

Every V2 context assembly SHALL include an audit record with included object IDs, excluded categories, policy version, projection version, estimated context size, and violation status.

#### Scenario: Unknown visibility is encountered

- **WHEN** a canonical case object has an unrecognized visibility value
- **THEN** context assembly excludes that object from actor-facing context
- **AND** the audit record marks a violation and records the unknown visibility exclusion

### Requirement: V2 role access policies fail closed

V2 access policy SHALL restrict context by actor role, node purpose, target witness, and visibility scope.

#### Scenario: Restricted material belongs to another role

- **WHEN** a lawyer, witness, judge, or jury context is assembled
- **THEN** evaluator-only truth, coach-only references, opposing private material, and non-target witness knowledge are excluded
