from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from courtroom_domain import CaseFile

from .models import SimulationCompletion, SimulationJob
from .queues import CompletionQueue
from .repositories import CaseFileReader, SimulationRunWriter


def run_simulation(
    job: SimulationJob,
    case_files: CaseFileReader,
    runs: SimulationRunWriter,
    completions: CompletionQueue,
) -> None:
    try:
        runs.mark_running(job.simulation_run_id)
        case_file = case_files.get(job.case_file_id)
        if case_file is None:
            raise RuntimeError(f"Case file not found: {job.case_file_id}")

        completion = SimulationCompletion(
            simulation_run_id=job.simulation_run_id,
            status="completed",
            result=_run_trial(case_file),
        )
    except Exception as exc:
        completion = SimulationCompletion(
            simulation_run_id=job.simulation_run_id,
            status="failed",
            error_message=str(exc),
        )

    completions.enqueue_completion(completion)


def _run_trial(case_file: CaseFile) -> dict[str, object]:
    run_trial, request_type = _load_agent_service_contract()

    response = run_trial(request_type(case_file=case_file))
    return response.model_dump(mode="json")


def _load_agent_service_contract() -> tuple[Callable[[object], object], type]:
    agent_service_root = Path(__file__).resolve().parents[3] / "agent-service"
    if agent_service_root.exists():
        sys.path.insert(0, str(agent_service_root))

    from src.service import run_trial
    from src.utils.types import RunTrialRequest

    return run_trial, RunTrialRequest
