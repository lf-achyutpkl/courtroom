from __future__ import annotations

from typing import Protocol

from ..models.completions import SimulationCompletion


class CompletionQueue(Protocol):
    def enqueue_completion(self, completion: SimulationCompletion) -> None:
        """Enqueue the simulation completion payload for database persistence."""


class RqCompletionQueue:
    def __init__(
        self,
        redis_url: str,
        queue_name: str = "simulation_results",
    ) -> None:
        self.redis_url = redis_url
        self.queue_name = queue_name

    def enqueue_completion(self, completion: SimulationCompletion) -> None:
        from redis import Redis
        from rq import Queue

        redis_connection = Redis.from_url(self.redis_url)
        queue = Queue(self.queue_name, connection=redis_connection)
        queue.enqueue(
            "worker_service.jobs.completion.apply_completion_message",
            completion.model_dump(mode="json"),
        )
