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

## Running unit test

```bash
make test
```
