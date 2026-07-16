from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from uuid import UUID

from courtroom_domain import CaseFile

from ..repositories.case_files import CaseFileRepository
from ..repositories.simulation_runs import SimulationRunRepository


@dataclass(frozen=True)
class SimulationGenerationJob:
    simulation_run_id: UUID
    case_file_id: UUID


def execute_generation_stage(
    job: SimulationGenerationJob,
    case_files: CaseFileRepository,
    runs: SimulationRunRepository,
) -> None:
    try:
        runs.mark_running(job.simulation_run_id)
        case_file = case_files.get(job.case_file_id)
        if case_file is None:
            raise RuntimeError(f"Case file not found: {job.case_file_id}")

        runs.store_result(
            job.simulation_run_id,
            _run_trial(case_file.case_file),
        )
    except Exception as exc:
        _mark_failed(runs, job.simulation_run_id, exc)
        raise


def finalize_generation_stage(
    simulation_run_id: UUID,
    runs: SimulationRunRepository,
) -> None:
    try:
        run = runs.get(simulation_run_id)
        if run is None:
            raise RuntimeError(f"Simulation run not found: {simulation_run_id}")
        if run.result is None:
            raise RuntimeError(
                f"Simulation run {simulation_run_id} has no generated result to persist."
            )

        runs.mark_completed(simulation_run_id, run.result)
    except Exception as exc:
        _mark_failed(runs, simulation_run_id, exc)
        raise


def _mark_failed(
    runs: SimulationRunRepository,
    simulation_run_id: UUID,
    exc: Exception,
) -> None:
    try:
        runs.mark_failed(simulation_run_id, str(exc))
    except Exception:
        pass


def _run_trial(case_file: CaseFile) -> dict[str, object]:
    run_trial, request_type = _load_agent_service_contract()
    response = run_trial(request_type(case_file=case_file))
    return response.model_dump(mode="json")


def _load_agent_service_contract() -> tuple[Callable[[object], object], type]:
    agent_service_root = Path(__file__).resolve().parents[4] / "agent-service"
    if agent_service_root.exists():
        sys.path.insert(0, str(agent_service_root))

    from src.service import run_trial
    from src.utils.types import RunTrialRequest

    return run_trial, RunTrialRequest
