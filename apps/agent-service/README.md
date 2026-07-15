# Agent Service

Reserved workspace for the Python and LangGraph runtime behind the courtroom simulator.

## Intended Responsibilities

- build and run multi-agent trial simulations
- perform retrieval and evidence grounding
- produce case, verdict, and playback artifacts for the frontend

## Status

This workspace is actively being scaffolded.

## Local Development

Install dependencies and the LangGraph CLI with:

```bash
uv sync
```

Start the LangGraph dev server with:

```bash
uv run langgraph dev
```

## Running Unit Tests

```bash
make test
```

## Evaluation Dataset

The domain evaluation dataset lives at `evals/domain_evaluation_dataset.json`.
It contains three active synthetic scenarios for:

- normal evidence-backed evaluation
- contradiction or unsupported-claim evaluation
- adversarial or unsafe-content evaluation

Runtime inputs are stored in each case's `case_file`. Evaluator-only ground truth stays in `reference` so the trial runtime does not receive scoring hints.

## Baseline Evaluation

Run the seeded baseline workflow with:

```bash
make eval-baseline
```

The command loads the default dataset, sends each `case_file` through `run_trial`, captures deterministic validation failures per case, and writes a new timestamped JSON report under `evals/reports/`.

Reports include dataset, graph, prompt, model, evaluator, per-case result, queue decision, alert summary, aggregate metric, and creation timestamp fields. Each report also gets a sibling artifact directory named after the report stem, with generated trial outputs under `outputs/`; per-case results include `generated_output_path` for cross-checking transcript content against evaluator findings.

Run the same baseline with the LLM-as-judge rubric enabled with:

```bash
OPENAI_API_KEY=... make eval-baseline-rubric
```

This target uses `gpt-4o` as the rubric judge and makes real OpenAI API calls.

To see traces in LangSmith, export tracing configuration before running the eval:

```bash
export LANGSMITH_TRACING=true
export LANGCHAIN_TRACING_V2=true
export LANGSMITH_API_KEY=...
export LANGSMITH_PROJECT=courtroom-simulation-local
export LANGCHAIN_PROJECT=courtroom-simulation-local
OPENAI_API_KEY=... make eval-baseline-rubric
```

When LangSmith tracing is enabled, the run metadata includes `langsmith_trace_id` so reports can be correlated with the trace.

## Promptfoo Adversarial Suite

Validate the promptfoo suite coverage without running promptfoo:

```bash
make validate-promptfoo-suite
```

Run the manual adversarial suite with:

```bash
make promptfoo-adversarial
```

The promptfoo command is intentionally manual for now. It covers role confusion, contradiction injection, unsupported legal claims, malformed evidence references, and unsafe-content prompts. Promptfoo failures return a non-zero exit code according to the configured blocking assertions.

## Rubric Evaluators

Rubric scoring is structured by dimension:

- legal grounding: threshold `0.75`
- procedural realism: threshold `0.70`
- role adherence: threshold `0.80`
- contradiction handling: threshold `0.75`
- verdict support: threshold `0.80`
- unsafe-content handling: threshold `0.90`

The default judge model is `gpt-4o`. The rubric evaluator accepts an injected judge dependency, so tests and future providers can supply a compatible callable without changing scoring orchestration.

## Monitoring And Review

Queue records are created for deterministic failures, high-severity rule/reference failures, rubric threshold failures, sampled runs, and alert-worthy runs. GitHub Issues sync is optional and isolated behind a client boundary. Configure repository, labels, assignees, issue template, and authentication in the caller or deployment layer before enabling sync.

The default sampling policy is no automatic sampling unless a caller sets a percentage or tag match.

Weekly review should inspect:

- sampled runs
- escalated runs
- severe alerts
- rubric failures
- unresolved annotation queue items
- linked GitHub Issues
- baseline regression summaries

Record one outcome per reviewed item:

- dataset update
- evaluator threshold change
- prompt or runtime fix
- GitHub Issue follow-up
- no action
