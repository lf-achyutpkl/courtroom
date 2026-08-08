## ADDED Requirements

### Requirement: Guide participant witness selection before trial start

The participation page SHALL show witnesses assigned to the selected participant side for the chosen case, let the participant select and order them, and prevent trial creation until at least one eligible witness is selected.

#### Scenario: Participant chooses witness order
- **WHEN** a participant selects a case and side with eligible witnesses
- **THEN** the page lists the eligible witnesses, allows an ordered selection, and sends the selected IDs when starting the trial

#### Scenario: No eligible participant witnesses
- **WHEN** the selected case has no witnesses assigned to the selected side
- **THEN** the page explains that the case needs an eligible witness and does not offer an enabled start action

### Requirement: Present the live proceeding at graph pauses

The participation page SHALL render `liveTranscript` in chronological order and refresh it while the run progresses. It SHALL preserve already visible turns across polling responses and identify the speaker and scene for each turn.

#### Scenario: Active examination contains unfinalized turns
- **WHEN** a run-detail poll returns active-witness question, answer, objection, or ruling turns
- **THEN** the page displays those turns before the witness loop completes

### Requirement: Render an action-specific participant card

The participation page SHALL use the typed pending-turn instruction to state the required action and show only applicable controls. It SHALL provide an accessible live announcement when the required action changes.

#### Scenario: Participant must ask a witness question
- **WHEN** the pending action is `question`
- **THEN** the page identifies the witness and direct or cross phase, asks the participant to record a question, provides a final-question control, and does not show a no-objection control

#### Scenario: Participant can object
- **WHEN** the pending action is `objection`
- **THEN** the page shows Record objection and No objection — continue controls alongside the relevant live proceeding context

#### Scenario: Participant must make an opening or closing
- **WHEN** the pending action is `opening` or `closing`
- **THEN** the page asks the participant to record that statement and does not describe it as an objection
