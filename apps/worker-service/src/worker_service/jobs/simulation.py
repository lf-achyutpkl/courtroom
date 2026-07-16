from __future__ import annotations

from uuid import UUID

from ..core.config import get_database_url, get_redis_url
from ..models.jobs import SimulationJob
from ..queues.simulation_results import RqCompletionQueue
from ..repositories.case_files import PostgresCaseFileReader
from ..repositories.simulation_runs import PostgresSimulationRunWriter
from ..services.simulation_runner import run_simulation


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
