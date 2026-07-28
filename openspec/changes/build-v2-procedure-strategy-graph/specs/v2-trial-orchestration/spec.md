## ADDED Requirements

### Requirement: V2 procedure controls trial state
The V2 engine SHALL use deterministic procedure state and policy records to determine the current phase, active actor, allowed action types, evidence admission state, objection state, and ruling records.

#### Scenario: Invalid action is rejected
- **WHEN** a trial actor requests an action that is not allowed for the actor role, node purpose, or current phase
- **THEN** the procedure policy rejects the action before any courtroom output is produced

### Requirement: V2 contexts isolate adjudicator roles
The V2 engine SHALL assemble trial judge and jury contexts from procedurally available trial-record material rather than complete canonical case packages.

#### Scenario: Jury context excludes unadmitted material
- **WHEN** jury context is assembled during trial execution
- **THEN** it contains only admitted evidence, testimony summaries, stipulations, instructions, permitted arguments, and verdict form records

#### Scenario: Judge ruling context is limited
- **WHEN** judge context is assembled for a pending objection or evidence ruling
- **THEN** it contains the admitted record plus disputed material needed for the current ruling

### Requirement: V2 strategy planning is side-reusable and role-safe
The V2 engine SHALL create party strategy records through a reusable planner that validates objectives, witness plans, evidence plans, and opponent risks against actor context, legal elements, available facts, disclosed evidence, and procedure.

#### Scenario: Strategy cannot use hidden opponent material
- **WHEN** a side strategy references a fact, evidence item, witness, or objective unavailable to that side
- **THEN** strategy validation fails closed and records the invalid reference

### Requirement: V2 graph runs a minimum practical structural trial
The `trial-v2-ai-ai` graph SHALL execute initialization, case analysis, side planning, opening, witness loop, closing record, closing phase, deliberation, and evaluation as structured phase outputs.

#### Scenario: Structural graph completes
- **WHEN** the V2 AI-vs-AI graph is invoked with the reference case
- **THEN** it reaches evaluation with recorded phase outputs and replay-friendly courtroom events

### Requirement: V2 witness examination separates tactics from language
The witness examination flow SHALL separate examination objective selection, tactical action planning, action validation, question generation, objection handling, judge ruling, witness answer, answer validation, evidence updates, contradiction detection, and objective progress assessment.

#### Scenario: Question generation receives only an execution brief
- **WHEN** a witness question is generated
- **THEN** the generation step receives a tactical execution brief and does not receive the complete party strategy

#### Scenario: Witness answer validation distinguishes contradiction from hallucination
- **WHEN** a witness answer introduces unsupported information
- **THEN** validation classifies it as hallucination unless it conflicts with known witness knowledge or admitted testimony in a way that forms an intentional contradiction signal
