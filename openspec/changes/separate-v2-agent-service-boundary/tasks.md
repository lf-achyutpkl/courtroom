## 1. Engine Boundary

- [x] 1.1 Remove LangGraph runtime dependencies and Studio config from `courtroom-engine`.
- [x] 1.2 Remove graph entrypoints and orchestration modules from `courtroom-engine`.
- [x] 1.3 Add engine boundary tests that reject graph runtime surface area.

## 2. Agent Service V2

- [x] 2.1 Create `apps/agent-service-v2` with package, Makefile, docs, and LangGraph config.
- [x] 2.2 Move AI-vs-AI trial and witness-loop graph orchestration into `agent-service-v2`.
- [x] 2.3 Move standalone evaluation graph orchestration into `agent-service-v2`.
- [x] 2.4 Reserve namespaces for future AI-vs-human and human-vs-human flows.

## 3. Verification

- [x] 3.1 Add V2 app tests for trial, witness-loop, evaluation, and graph registration.
- [x] 3.2 Run targeted engine and V2 app tests.
