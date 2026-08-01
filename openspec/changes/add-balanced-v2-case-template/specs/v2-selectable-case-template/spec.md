## ADDED Requirements

### Requirement: V2 invocation selects an authored template

The V2 AI-vs-AI graph SHALL compile an `AuthoredCaseTemplate` supplied in its initial state and SHALL retain the reference template as its default when none is supplied.

#### Scenario: Caller supplies a balanced template

- **WHEN** an AI-vs-AI invocation starts with `case_template` set
- **THEN** the runtime case package SHALL use that template's metadata and compiled evidence

#### Scenario: Caller omits a template

- **WHEN** an AI-vs-AI invocation starts without `case_template`
- **THEN** the runtime SHALL compile the existing reference template

### Requirement: Balanced prototype-theft fixture

The courtroom engine SHALL provide a criminal authored fixture with contested identity and intent, materially relevant evidence for each party, and recorded contradictions suitable for evaluation and coaching.

#### Scenario: Fixture compiles

- **WHEN** the balanced prototype-theft fixture is passed to `CaseCompiler`
- **THEN** compilation SHALL succeed with prosecution and defense parties, witnesses, evidence, and witness knowledge

#### Scenario: Decisive evidence is contested

- **WHEN** the fixture is compiled for a trial run
- **THEN** its derived intelligence SHALL contain the fixture's expected access-and-timing contradiction
