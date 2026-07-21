# Courtroom Simulation

[![Python package](https://github.com/lf-achyutpkl/courtroom/actions/workflows/python-package.yml/badge.svg)](https://github.com/lf-achyutpkl/courtroom/actions/workflows/python-package.yml)

AI courtroom simulation built with `LangGraph`, `FastAPI`, `Next.js`, and `RQ`. It generates evidence-grounded trials, renders spoken verdicts, and turns the result into a replayable courtroom experience.

`LangGraph` • `multi-agent orchestration` • `RAG-grounded reasoning` • `evaluation pipeline` • `async workers` • `PixiJS playback`

> ⚖️ **Version 2 coming**
>
> V2 turns this into a live courtroom training loop: a human argues the case in real time against an LLM-powered opposing counsel, an LLM judge delivers the verdict, and the system returns structured feedback on argument quality, performance, strengths, and weaknesses.

## 🔎 System Flow

```text
Case-building chat
   |
   v
LangGraph case editor
   |- interpret user request
   |- apply structured edit to stored case file
   `- narrate the change back to the UI
   |
   v
Case file editor
   |- metadata
   |- witnesses
   |- evidence
   `- disputed facts
   |
   v
Simulation start
   |
   v
LangGraph trial runtime
   |- load case template
   |- parallel strategy planning
   |- witness queue construction
   |- witness examination subgraph
   `- verdict generation
   |
   v
Evaluation layer
   |- evidence reference checks
   |- contradiction probes
   |- unsupported-claim detection
   `- rubric scoring / review signals
   |
   v
FastAPI + Redis/RQ pipeline
   |- persist run
   |- queue simulation stage
   `- queue audio stage
   |
   v
Frontend playback
   |- transcript
   |- case summary
   `- PixiJS courtroom presentation
```

## 🧠 Case File Generation

Case creation starts in a conversational editor, not a raw form.

- The frontend exposes a chat-first case editor with a synchronized card-based workspace for case metadata, witnesses, evidence, and disputed facts.
- Chat messages are sent to a case-editor endpoint, along with the currently selected card when the user wants to focus a specific item.
- The LangGraph case editor runs a two-step flow:
  - `process_edit` interprets the user request and converts it into a typed case edit result
  - `narrate` turns that edit into a short natural-language update for the chat timeline
- The backend applies edits against the stored case file revision instead of treating the chat transcript as the source of truth.
- The UI reflects structured diffs, jump-to-change actions, review actions, and undo support around AI-generated edits.

This keeps the case-building flow grounded in the saved case file while still letting the user work conversationally.

## ⚖️ Trial Graph

The trial runtime is implemented as a LangGraph state graph with explicit phases and routing.

```text
START
  -> load_case_template
  -> prosecution_strategy
  -> defense_strategy
     [parallel execution]
  -> build_witness_queue
  -> opening_prosecution
  -> opening_defense
  -> select_next_witness
     -> examine_witness or summarize_trial_transcript
  -> closing_prosecution
  -> closing_defense
  -> verdict
  -> END
```

- `prosecution_strategy` and `defense_strategy` run in parallel after the case template is loaded, then join before witness queue construction.
- Witness handling is delegated into a dedicated subgraph instead of flattening examination logic into the main trial graph.
- The witness subgraph routes through question asking, objection checks, judge rulings, witness answers, and cross-examination swaps with conditional edges.
- The graph composes deterministic orchestration with structured model outputs at each node.

## 🎯 Core AI Capabilities

| Capability | Current implementation |
| --- | --- |
| Case-building flow | LangGraph case editor that converts chat requests into typed case-file mutations |
| Multi-agent trial flow | LangGraph runtime for strategy planning, witness examination, rulings, closings, and verdicts |
| Subgraph composition | Dedicated witness examination subgraph with conditional routing |
| Parallel node execution | Prosecution and defense strategy nodes run in parallel before the trial continues |
| Evidence grounding | Verdict and transcript logic use case evidence and tracked evidence IDs |
| Structured outputs | Pydantic-shaped model outputs with node-level token controls |
| Evaluation | Dataset-backed checks for evidence support, contradiction handling, verdict support, and unsafe or unsupported claims |
| Adversarial testing | Manual `promptfoo` suite for role confusion, contradiction injection, malformed evidence references, and unsafe prompts |
| Observability | Optional LangSmith tracing plus evaluation reports written to `apps/agent-service/evals/reports/` |

## ⚙️ System Design

### AI runtime

- `apps/agent-service` owns the LangGraph simulation runtime, the case editor graph, prompts, evaluation logic, and baseline/adversarial testing.

### API and worker orchestration

- `apps/api-service` owns the FastAPI boundary, persistence, Redis/RQ queues, the staged simulation-to-audio workflow, and the case-file message boundary used by the editor.

### Frontend

- `apps/web-app` owns the conversational case editor, card-based case workspace, simulation browsing, and the courtroom playback UI built on Next.js and PixiJS.

### Shared domain layer

- `packages/python-domain` holds shared Python domain models used across services.

## 🎙️ Product Surface

The current frontend exposes two main engineering surfaces:

- a conversational case editor with structured case-file cards and simulation readiness checks
- a simulation playback view with transcript, metadata, and staged courtroom presentation

The case editor and playback views are separate flows connected by the stored case file and simulation run contracts.

## ✅ AI Evaluation And Safety Posture

- Seeded baseline evaluations run against a domain dataset in `apps/agent-service/evals/domain_evaluation_dataset.json`.
- Rule-based evaluators check evidence references, verdict support, contradiction probes, unsupported claims, and required trial phases.
- A manual `promptfoo` suite exercises adversarial scenarios such as role confusion and contradiction injection.
- Rubric scoring can use an LLM judge to assess legal grounding, procedural realism, role adherence, contradiction handling, verdict support, and unsafe-content handling.
- Queue review records can be created for failures, severe alerts, and sampled runs.

## 🛠️ Tech Stack

| Area | Tools |
| --- | --- |
| AI orchestration | `LangGraph`, `LangChain`, `OpenAI` models |
| Evaluation | `promptfoo`, rubric evaluators, optional `LangSmith` tracing |
| Backend | `FastAPI`, `SQLAlchemy`, `Postgres`, `Redis`, `RQ`, `Python` |
| Frontend | `Next.js`, `React`, `TypeScript`, `PixiJS` |
| Dev workflow | `Docker Compose`, `Make`, `uv`, `pnpm` |

## 🚀 Run It Locally

### Fastest path

```bash
cp apps/web-app/.env.example apps/web-app/.env
cp apps/api-service/.env.example apps/api-service/.env
cp apps/agent-service/.env.example apps/agent-service/.env
docker compose up --build
```

Main endpoints:

- Web app: `http://localhost:3000`
- API service: `http://localhost:8000`

### Workspace commands

```bash
make web-dev
make api-dev
make agent-dev
make worker
```

## 📁 Repository Shape

```text
apps/
  agent-service   LangGraph runtime, case editor, prompts, evals
  api-service     FastAPI API, Redis/RQ workers, persistence
  web-app         Case editor, simulation library, courtroom playback
packages/
  python-domain   Shared Python domain models
```

## 📌 Roadmap

- Add live human-vs-model courtroom mode for V2
- Return structured post-trial coaching on persuasion, evidence use, and weaknesses
- Expand simulation-run browsing and review workflows
- Harden observability and review tooling around failed or low-quality runs
