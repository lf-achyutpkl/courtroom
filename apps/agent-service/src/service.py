from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .utils.config import TRIAL_CONFIG
from .utils.graph import build_graph
from .utils import llm
from .utils.state import TrialState
from .utils.types import RunMetadata, RunTrialRequest, RunTrialResponse
from .utils.validation import validate_trial_run


_trial_graph = build_graph()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_initial_state(request: RunTrialRequest) -> TrialState:
    return TrialState(
        case_file=request.case_file,
        run_id=str(uuid4()),
        run_started_at=_utc_now_iso(),
    )


def run_trial(request: RunTrialRequest) -> RunTrialResponse:
    initial_state = _build_initial_state(request)
    result = _trial_graph.invoke(initial_state)
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
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=int((completed_at_dt - started_at_dt).total_seconds() * 1000),
        deterministic_validation_passed=False,
    )
    validate_trial_run(result_state, run_metadata)
    return RunTrialResponse(
        full_trial_transcript=result_state.full_trial_transcript,
        run=run_metadata.model_copy(
            update={"deterministic_validation_passed": True}
        ),
    )
