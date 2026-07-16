from __future__ import annotations

from typing import Protocol
from uuid import UUID


class SimulationQueue(Protocol):
    def enqueue_simulation(
        self,
        simulation_run_id: UUID,
        case_file_id: UUID,
    ) -> None:
        """Enqueue a simulation run for worker execution."""


class RqSimulationQueue:
    def __init__(
        self,
        redis_url: str,
        queue_name: str = "simulation_jobs",
    ) -> None:
        self.redis_url = redis_url
        self.queue_name = queue_name

    def enqueue_simulation(
        self,
        simulation_run_id: UUID,
        case_file_id: UUID,
    ) -> None:
        from redis import Redis
        from rq import Queue

        redis_connection = Redis.from_url(self.redis_url)
        queue = Queue(self.queue_name, connection=redis_connection)
        queue.enqueue(
            "worker_service.jobs.simulation.run_simulation_job",
            str(simulation_run_id),
            str(case_file_id),
        )
