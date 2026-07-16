from __future__ import annotations

from ..core.config import get_database_url, get_redis_url
from ..repositories.case_files import CaseFileRepository, PostgresCaseFileRepository
from ..repositories.simulation_runs import (
    PostgresSimulationRunRepository,
    SimulationRunRepository,
)
from ..services.simulation_queue import RqSimulationQueue, SimulationQueue


def get_case_file_repository() -> CaseFileRepository:
    return PostgresCaseFileRepository(get_database_url())


def get_simulation_run_repository() -> SimulationRunRepository:
    return PostgresSimulationRunRepository(get_database_url())


def get_simulation_queue() -> SimulationQueue:
    return RqSimulationQueue(get_redis_url())
