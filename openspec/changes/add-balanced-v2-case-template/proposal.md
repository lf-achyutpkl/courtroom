## Why

The prompt-enabled V2 trial graph can run only a hard-coded reference fixture and Studio does not configure a live prompt executor. A selectable, balanced criminal case is needed to exercise advocacy, evaluation, and coaching under realistic but genuinely contestable conditions.

## What Changes

- Add a reusable balanced prototype-theft `AuthoredCaseTemplate` fixture for V2 trial runs.
- Allow the V2 AI-vs-AI state to supply a case template instead of always selecting the reference case.
- Configure the Studio AI-vs-AI graph with the OpenAI Responses prompt executor.
- Preserve the reference case as the default when no template is supplied.

## Capabilities

### New Capabilities

- `v2-selectable-case-template`: Select and execute compiled V2 case templates, including a balanced criminal coaching fixture.
- `v2-live-prompt-studio-runtime`: Configure the Studio V2 graph for live structured prompt execution.

### Modified Capabilities

- None.

## Impact

- `packages/courtroom-engine` gains a reusable fixture only; it remains flow agnostic.
- `apps/agent-service-v2` gains state-level case selection and Studio provider wiring.
- The legacy web/API `CaseFile` contract remains unchanged and is not adapted by this change.
