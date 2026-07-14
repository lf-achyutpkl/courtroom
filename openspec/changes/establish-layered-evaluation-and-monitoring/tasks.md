## 1. OpenSpec And Contract Foundation

- [x] 1.1 Document the layered evaluation foundation and new response contract in OpenSpec artifacts
- [x] 1.2 Update the agent-service contract docs to include run metadata, deterministic validation, and future monitoring phases

## 2. Runtime Metadata And Telemetry

- [x] 2.1 Add agent-service types for run metadata and node telemetry records
- [x] 2.2 Instrument the service entrypoint, trial state, and LLM helpers to capture run and node telemetry consistently
- [x] 2.3 Propagate phase and witness context into node telemetry for witness-examination flows

## 3. Deterministic Validation

- [x] 3.1 Implement deterministic validators for transcript structure, runtime sequencing, and response contract invariants
- [x] 3.2 Enforce deterministic validation as a hard gate before returning a successful trial response

## 4. Verification

- [x] 4.1 Add or update unit tests for run metadata and deterministic validation behavior
- [x] 4.2 Run targeted agent-service tests covering the new validation and telemetry paths
