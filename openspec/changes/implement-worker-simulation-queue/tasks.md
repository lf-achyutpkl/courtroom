## 1. Database

- [x] 1.1 Add a migration for `simulation_runs`
- [x] 1.2 Include status, timestamps, JSON result, and error message fields

## 2. API Service

- [x] 2.1 Add simulation run repository protocols and Postgres implementation
- [x] 2.2 Add queue protocol and Redis/RQ implementation for simulation jobs
- [x] 2.3 Add `POST /start-simulation`
- [x] 2.4 Add tests for success, missing case file, and enqueue failure

## 3. Worker Service

- [x] 3.1 Add worker-service Python package scaffold
- [x] 3.2 Add queue payload models and queue adapters
- [x] 3.3 Add simulation job handler that calls the agent-service runtime
- [x] 3.4 Add completion consumer that updates simulation run status

## 4. Verification

- [x] 4.1 Run API service unit tests
- [x] 4.2 Add focused worker unit tests for success and failure paths
- [x] 4.3 Update local docs and environment examples
