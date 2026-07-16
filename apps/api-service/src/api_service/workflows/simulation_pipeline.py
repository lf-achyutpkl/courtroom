from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Protocol
from uuid import UUID

from courtroom_domain import CaseFile

from ..repositories.case_files import CaseFileRepository
from ..repositories.simulation_runs import SimulationRunRepository
from ..services.tts import SimulationAudioService


@dataclass(frozen=True)
class SimulationGenerationJob:
    simulation_run_id: UUID
    case_file_id: UUID


class SupportsModelDump(Protocol):
    def model_dump(self, *, mode: str) -> dict[str, object]: ...


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


def execute_audio_generation_stage(
    simulation_run_id: UUID,
    *,
    case_files: CaseFileRepository,
    runs: SimulationRunRepository,
    audio_service: SimulationAudioService,
) -> None:
    try:
        run = runs.get(simulation_run_id)
        if run is None:
            raise RuntimeError(f"Simulation run not found: {simulation_run_id}")
        if run.result is None:
            raise RuntimeError(
                f"Simulation run {simulation_run_id} has no generated result for audio synthesis."
            )

        case_file = case_files.get(run.case_file_id)
        if case_file is None:
            raise RuntimeError(f"Case file not found: {run.case_file_id}")

        runs.mark_generating_audio(simulation_run_id)
        audio_manifest, audio_storage = audio_service.generate_for_run(
            simulation_run_id=simulation_run_id,
            case_file=case_file.case_file,
            simulation_result=run.result,
        )
        runs.store_audio_artifacts(
            simulation_run_id,
            audio_manifest=audio_manifest,
            audio_storage=audio_storage,
        )
        runs.mark_completed(simulation_run_id)
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
    run_trial, request_factory = _load_agent_service_contract()
    response = run_trial(request_factory(case_file=case_file))
    return response.model_dump(mode="json")


@lru_cache(maxsize=1)
def _load_agent_service_contract() -> tuple[
    Callable[[object], SupportsModelDump], Callable[..., object]
]:
    try:
        service_module = importlib.import_module("src.service")
        types_module = importlib.import_module("src.utils.types")
    except ModuleNotFoundError as exc:
        agent_service_root = Path(__file__).resolve().parents[4] / "agent-service"
        if not agent_service_root.exists():
            raise RuntimeError(
                f"Agent service workspace not found at {agent_service_root}."
            ) from exc

        package_name = "_agent_service_runtime"
        package_root = agent_service_root / "src"
        package_init = package_root / "__init__.py"
        package = sys.modules.get(package_name)
        if package is None:
            spec = importlib.util.spec_from_file_location(
                package_name,
                package_init,
                submodule_search_locations=[str(package_root)],
            )
            if spec is None or spec.loader is None:
                raise RuntimeError(
                    f"Unable to load agent service package from {package_root}."
                ) from exc

            package = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = package
            spec.loader.exec_module(package)

        service_module = importlib.import_module(f"{package_name}.service")
        types_module = importlib.import_module(f"{package_name}.utils.types")

    return service_module.run_trial, types_module.RunTrialRequest
