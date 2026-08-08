from __future__ import annotations

from ..core.config import (
    get_database_url,
    get_r2_access_key_id,
    get_r2_bucket_name,
    get_r2_endpoint_url,
    get_r2_public_base_url,
    get_r2_region,
    get_r2_secret_access_key,
    get_redis_url,
)
from ..queue.interactive_trial import InteractiveTrialQueue, RqInteractiveTrialQueue
from ..queue.simulation_pipeline import RqSimulationQueue, SimulationQueue
from ..repositories.case_file_messages import (
    CaseFileMessageRepository,
    PostgresCaseFileMessageRepository,
)
from ..repositories.case_files import CaseFileRepository, PostgresCaseFileRepository
from ..repositories.interactive_trial_runs import PostgresInteractiveTrialRunRepository
from ..repositories.simulation_runs import (
    PostgresSimulationRunRepository,
    SimulationRunRepository,
)
from ..services.storage import R2ObjectStorageService


def get_case_file_repository() -> CaseFileRepository:
    return PostgresCaseFileRepository(get_database_url())


def get_case_file_message_repository() -> CaseFileMessageRepository:
    return PostgresCaseFileMessageRepository(get_database_url())


def get_simulation_run_repository() -> SimulationRunRepository:
    return PostgresSimulationRunRepository(get_database_url())


def get_simulation_queue() -> SimulationQueue:
    return RqSimulationQueue(get_redis_url())


def get_interactive_trial_repository() -> PostgresInteractiveTrialRunRepository:
    return PostgresInteractiveTrialRunRepository(get_database_url())


def get_interactive_trial_queue() -> InteractiveTrialQueue:
    return RqInteractiveTrialQueue(get_redis_url())


def get_object_storage() -> R2ObjectStorageService:
    return R2ObjectStorageService(
        bucket_name=get_r2_bucket_name(),
        endpoint_url=get_r2_endpoint_url(),
        access_key_id=get_r2_access_key_id(),
        secret_access_key=get_r2_secret_access_key(),
        public_base_url=get_r2_public_base_url(),
        region_name=get_r2_region(),
    )
