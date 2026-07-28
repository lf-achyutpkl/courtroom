## 1. Procedure And Events

- [x] 1.1 Add deterministic procedure, evidence admission, objection, ruling, and event domain models.
- [x] 1.2 Add procedure policy helpers for role/phase/node-purpose allowed actions and validation failures.
- [x] 1.3 Wire context assembly to procedure policies and add judge/jury record-limited projections.

## 2. Strategy Planner

- [x] 2.1 Add party strategy, case theory, objective, witness plan, evidence plan, opponent risk, and runtime objective models.
- [x] 2.2 Add deterministic reusable side planner and strategy validator.
- [x] 2.3 Add staged context/brief DTOs so tactical action planning and question generation stay separated.

## 3. V2 Graph And Witness Examination

- [x] 3.1 Move graph builders into orchestration modules while preserving the public `build_v2_ai_ai_graph` entrypoint.
- [x] 3.2 Implement the minimum practical V2 graph phases with structured phase outputs and replay-friendly events.
- [x] 3.3 Implement the structured witness examination flow with deterministic answer validation and state updates.

## 4. Verification And Docs

- [x] 4.1 Add package tests for procedure policies, role isolation, strategy validation, witness examination, and V2 graph completion.
- [x] 4.2 Update V2 task documentation to mark completed items for this slice.
- [x] 4.3 Run targeted package and agent-service V2 tests.
