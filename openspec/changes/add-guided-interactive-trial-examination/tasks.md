## 1. Interactive runtime and persistence

- [x] 1.1 Extend the initial interactive execution contract to accept the persisted ordered human witness plan and add unit coverage for its propagation and validation failure handling.
- [x] 1.2 Add a backward-compatible interactive-run persistence field for the human witness plan, including repository mapping and migration coverage.
- [x] 1.3 Extend run creation validation to require unique witnesses belonging to the selected human side, persist the plan, and pass it through the RQ initial job.

## 2. Run read model and API contract

- [x] 2.1 Add public request and response schemas for `humanWitnessPlan`, `liveTranscript`, and typed pending-turn context, including witness and examination-phase details.
- [x] 2.2 Project pause-level `liveTranscript` from the stored graph snapshot, merging finalized and current-witness turns without duplication while retaining the existing `transcript` field.
- [x] 2.3 Normalize graph interrupts and snapshot data into action-specific pending-turn instructions for question, objection, opening, and closing turns.
- [x] 2.4 Add API and repository tests for valid/invalid witness plans, live transcript projection, and typed pending-turn responses.

## 3. Guided participation UI

- [x] 3.1 Extend the trial setup UI to show human-side witnesses for the selected case, support ordered selection, block empty selections, and explain cases with no eligible witnesses.
- [x] 3.2 Submit the selected witness IDs when creating a run and update the frontend run types for the expanded response contract.
- [x] 3.3 Extract a live proceeding transcript component that renders incremental turns accessibly and preserves visible context across polling refreshes.
- [x] 3.4 Replace the generic recording card with action-specific question, objection, opening, and closing instructions and controls, including witness identity and examination phase.
- [x] 3.5 Add frontend tests for guided setup validation, live witness transcript rendering, question-turn guidance, objection controls, and opening/closing guidance.

## 4. Verification and documentation

- [x] 4.1 Update the interactive participation API and UI documentation with the witness-plan, live-transcript, and pending-turn contracts.
- [x] 4.2 Run targeted agent-service, API-service, and web-app tests; run formatting/type checks; then validate the OpenSpec change with `openspec validate add-guided-interactive-trial-examination --strict`.
