from __future__ import annotations

from uuid import UUID

from .config import get_database_url, get_redis_url
from .models import SimulationJob
from .queues import RqCompletionQueue
from .repositories import PostgresCaseFileReader, PostgresSimulationRunWriter
from .runner import run_simulation


def run_simulation_job(simulation_run_id: str, case_file_id: str) -> None:
    database_url = get_database_url()
    run_simulation(
        SimulationJob(
            simulation_run_id=UUID(simulation_run_id),
            case_file_id=UUID(case_file_id),
        ),
        case_files=PostgresCaseFileReader(database_url),
        runs=PostgresSimulationRunWriter(database_url),
        completions=RqCompletionQueue(get_redis_url()),
    )
