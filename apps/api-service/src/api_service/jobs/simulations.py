from __future__ import annotations

from uuid import UUID

from ..core.config import get_database_url
from ..repositories.case_files import PostgresCaseFileRepository
from ..repositories.simulation_runs import PostgresSimulationRunRepository
from ..workflows.simulation_pipeline import (
    SimulationGenerationJob,
    execute_generation_stage,
    finalize_generation_stage,
)


def run_generation_stage(simulation_run_id: str, case_file_id: str) -> None:
    database_url = get_database_url()
    execute_generation_stage(
        SimulationGenerationJob(
            simulation_run_id=UUID(simulation_run_id),
            case_file_id=UUID(case_file_id),
        ),
        case_files=PostgresCaseFileRepository(database_url),
        runs=PostgresSimulationRunRepository(database_url),
    )


def persist_generation_stage(simulation_run_id: str) -> None:
    finalize_generation_stage(
        simulation_run_id=UUID(simulation_run_id),
        runs=PostgresSimulationRunRepository(get_database_url()),
    )
