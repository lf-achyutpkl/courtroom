from __future__ import annotations

from uuid import UUID

from ..core.config import get_database_url
from ..repositories.case_files import PostgresCaseFileRepository
from ..repositories.simulation_runs import PostgresSimulationRunRepository
from ..services.tts import create_simulation_audio_service
from ..workflows.simulation_pipeline import (
    SimulationGenerationJob,
    execute_audio_generation_stage,
    execute_generation_stage,
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


def generate_audio_stage(simulation_run_id: str) -> None:
    database_url = get_database_url()
    execute_audio_generation_stage(
        UUID(simulation_run_id),
        case_files=PostgresCaseFileRepository(database_url),
        runs=PostgresSimulationRunRepository(database_url),
        audio_service=create_simulation_audio_service(),
    )
