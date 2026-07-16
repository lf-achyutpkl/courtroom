from __future__ import annotations

from typing import Protocol
from uuid import UUID

RUN_TRIAL_JOB_TIMEOUT_SECONDS = 15 * 60  # 15 minutes


class SimulationQueue(Protocol):
    def enqueue_simulation(
        self,
        simulation_run_id: UUID,
        case_file_id: UUID,
    ) -> None:
        """Enqueue the chained simulation pipeline."""


class RqSimulationQueue:
    def __init__(
        self,
        redis_url: str,
        llm_queue_name: str = "simulation_llm",
        db_queue_name: str = "simulation_db",
    ) -> None:
        self.redis_url = redis_url
        self.llm_queue_name = llm_queue_name
        self.db_queue_name = db_queue_name

    def enqueue_simulation(
        self,
        simulation_run_id: UUID,
        case_file_id: UUID,
    ) -> None:
        from redis import Redis
        from rq import Queue

        redis_connection = Redis.from_url(self.redis_url)
        llm_queue = Queue(self.llm_queue_name, connection=redis_connection)
        db_queue = Queue(self.db_queue_name, connection=redis_connection)

        generation_job = None
        try:
            generation_job = llm_queue.enqueue(
                "api_service.jobs.simulations.run_generation_stage",
                str(simulation_run_id),
                str(case_file_id),
                job_timeout=RUN_TRIAL_JOB_TIMEOUT_SECONDS,
            )
            db_queue.enqueue(
                "api_service.jobs.simulations.persist_generation_stage",
                str(simulation_run_id),
                depends_on=generation_job,
            )
        except Exception:
            if generation_job is not None:
                try:
                    generation_job.delete()
                except Exception:
                    pass
            raise
