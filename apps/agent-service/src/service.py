from __future__ import annotations

from .utils.graph import build_graph
from .utils.state import TrialState
from .utils.types import RunTrialRequest, RunTrialResponse


_trial_graph = build_graph()


def _build_initial_state(request: RunTrialRequest) -> TrialState:
    return TrialState(case_file=request.case_file)


def run_trial(request: RunTrialRequest) -> RunTrialResponse:
    result = _trial_graph.invoke(_build_initial_state(request))
    result_state = (
        result if isinstance(result, TrialState) else TrialState.model_validate(result)
    )
    return RunTrialResponse(full_trial_transcript=result_state.full_trial_transcript)
