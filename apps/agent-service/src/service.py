from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from langchain_core.tracers.context import collect_runs

from .utils import llm
from .utils.config import TRIAL_CONFIG
from .utils.graph import build_graph
from .utils.state import TrialState
from .utils.types import RunMetadata, RunTrialRequest, RunTrialResponse
from .utils.validation import DeterministicValidationError, validate_trial_run

_trial_graph = build_graph()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _root_trace_id(traced_runs: Sequence[object]) -> str | None:
    for run in traced_runs:
        if getattr(run, "parent_run_id", None) is None:
            run_id = getattr(run, "id", None)
            return str(run_id) if run_id is not None else None
    if traced_runs:
        run_id = getattr(traced_runs[0], "id", None)
        return str(run_id) if run_id is not None else None
    return None


def _langsmith_tracing_enabled() -> bool:
    enabled_values = {"1", "true", "yes", "on"}
    return (
        os.getenv("LANGSMITH_TRACING", "").lower() in enabled_values
        or os.getenv("LANGCHAIN_TRACING_V2", "").lower() in enabled_values
    )


def _build_initial_state(request: RunTrialRequest) -> TrialState:
    return TrialState(
        case_file=request.case_file,
        run_id=str(uuid4()),
        run_started_at=_utc_now_iso(),
    )


def _run_trial_with_state(
    request: RunTrialRequest,
) -> tuple[RunTrialResponse, TrialState]:
    initial_state = _build_initial_state(request)
    with collect_runs() as runs_cb:
        result = _trial_graph.invoke(initial_state)
    langsmith_trace_id = (
        _root_trace_id(runs_cb.traced_runs) if _langsmith_tracing_enabled() else None
    )
    result_state = (
        result if isinstance(result, TrialState) else TrialState.model_validate(result)
    )
    completed_at = _utc_now_iso()
    started_at = (
        result_state.run_started_at or initial_state.run_started_at or completed_at
    )
    started_at_dt = datetime.fromisoformat(started_at)
    completed_at_dt = datetime.fromisoformat(completed_at)
    run_metadata = RunMetadata(
        run_id=result_state.run_id or initial_state.run_id or str(uuid4()),
        case_id=result_state.case_file.case_id,
        graph_version=TRIAL_CONFIG.graph_version,
        prompt_version=TRIAL_CONFIG.prompt_version,
        model_name=getattr(llm.fast_llm, "model_name", "unknown"),
        judge_model_name=getattr(llm.judge_llm, "model_name", "unknown"),
        environment=TRIAL_CONFIG.environment,
        langsmith_trace_id=langsmith_trace_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=int((completed_at_dt - started_at_dt).total_seconds() * 1000),
        deterministic_validation_passed=False,
    )
    response = RunTrialResponse(
        full_trial_transcript=result_state.full_trial_transcript,
        run=run_metadata,
    )
    try:
        validate_trial_run(result_state, run_metadata)
    except DeterministicValidationError as exc:
        exc.generated_output = response
        exc.node_telemetry = result_state.node_telemetry
        raise

    response = response.model_copy(
        update={
            "run": run_metadata.model_copy(
                update={"deterministic_validation_passed": True}
            )
        }
    )
    return response, result_state


def run_trial(request: RunTrialRequest) -> RunTrialResponse:
    response, _ = _run_trial_with_state(request)
    return response
