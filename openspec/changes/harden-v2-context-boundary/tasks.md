## 1. Package Structure

- [x] 1.1 Split flat V2 courtroom engine models into domain modules.
- [x] 1.2 Preserve compatibility exports for existing imports.

## 2. Context Boundary

- [x] 2.1 Add explicit DTOs for actor-facing model contexts.
- [x] 2.2 Add context audit records with included IDs, exclusions, policy/projection versions, estimated size, and violation status.
- [x] 2.3 Move access policy decisions into policy modules.

## 3. Verification

- [x] 3.1 Add regression tests for unknown visibility and restricted truth/material leakage.
- [x] 3.2 Add regression tests proving model-facing contexts use DTOs, not canonical package objects.
- [x] 3.3 Run targeted package and agent-service V2 tests.
