"""Checkpointed service contract for AI-vs-human trial execution.

This module is deliberately independent of FastAPI and RQ.  API workers own
transport, persistence of their public run records, and audio-object download;
the agent service owns only LangGraph invocation and its normalized outcome.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal

from courtroom_domain import CaseFile
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from pydantic import ValidationError

from ..utils.state import TrialState
from .graph import build_ai_human_graph


@dataclass(frozen=True)
class InteractiveExecutionResult:
    """A durable, API-worker-friendly view of one graph advancement."""

    status: Literal["awaiting_human", "completed"]
    state: dict[str, Any]
    interrupt: dict[str, Any] | None


@contextmanager
def build_interactive_postgres_checkpointer(
    database_url: str,
) -> Iterator[PostgresSaver]:
    """Create and initialize the checkpointer used by interactive workers."""

    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        checkpointer.setup()
        yield checkpointer


def execute_interactive_trial(
    *,
    thread_id: str,
    case_file: CaseFile | None = None,
    human_attorney_side: Literal["prosecution", "defense"] = "defense",
    human_witness_plan: list[str] | None = None,
    resume_payload: dict[str, object] | None = None,
    checkpointer: Any,
) -> InteractiveExecutionResult:
    """Start or resume exactly one checkpointed interactive trial thread.

    A new execution requires ``case_file``; resumption is intentionally only a
    ``Command(resume=...)`` against the stable thread id, preventing a retry
    from accidentally starting a second trial.
    """

    graph = build_ai_human_graph(checkpointer=checkpointer)
    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": "ai-vs-human",
        "metadata": {"langgraph_thread_id": thread_id, "trial_mode": "ai_vs_human"},
    }
    if resume_payload is None:
        if case_file is None:
            raise ValueError(
                "case_file is required for an initial interactive execution"
            )
        if not human_witness_plan:
            raise ValueError(
                "human_witness_plan is required for an initial interactive execution"
            )
        initial_state = TrialState(
            case_file=case_file,
            trial_mode="ai_vs_human",
            human_attorney_side=human_attorney_side,
            human_witness_plan=human_witness_plan or [],
        )
        raw_result = graph.invoke(initial_state, config=config)
    else:
        raw_result = graph.invoke(Command(resume=resume_payload), config=config)

    state = _normalise_state(raw_result, graph.get_state(config).values)
    interrupt = _normalise_interrupt(raw_result)
    return InteractiveExecutionResult(
        status="awaiting_human" if interrupt is not None else "completed",
        state=state,
        interrupt=interrupt,
    )


def _normalise_state(raw_result: object, persisted_state: object) -> dict[str, Any]:
    source = persisted_state if isinstance(persisted_state, dict) else raw_result
    if isinstance(source, TrialState):
        return source.model_dump(mode="json")
    if not isinstance(source, dict):
        return {}
    try:
        return TrialState.model_validate(source).model_dump(mode="json")
    except ValidationError:
        return {key: value for key, value in source.items() if key != "__interrupt__"}


def _normalise_interrupt(raw_result: object) -> dict[str, Any] | None:
    if not isinstance(raw_result, dict):
        return None
    raw_interrupts = raw_result.get("__interrupt__")
    if not isinstance(raw_interrupts, (list, tuple)) or not raw_interrupts:
        return None
    value = getattr(raw_interrupts[0], "value", raw_interrupts[0])
    return dict(value) if isinstance(value, dict) else None
