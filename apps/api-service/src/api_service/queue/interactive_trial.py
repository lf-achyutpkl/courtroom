from __future__ import annotations

from typing import Protocol
from uuid import UUID

INTERACTIVE_TRIAL_JOB_TIMEOUT_SECONDS = 15 * 60


class InteractiveTrialQueue(Protocol):
    def enqueue_initial(self, run_id: UUID) -> None: ...
    def enqueue_resume(self, run_id: UUID, turn_id: UUID) -> None: ...


class RqInteractiveTrialQueue:
    def __init__(self, redis_url: str, queue_name: str = "interactive_trial") -> None:
        self.redis_url = redis_url
        self.queue_name = queue_name

    def enqueue_initial(self, run_id: UUID) -> None:
        self._enqueue("api_service.jobs.interactive_trials.run_initial", str(run_id))

    def enqueue_resume(self, run_id: UUID, turn_id: UUID) -> None:
        self._enqueue(
            "api_service.jobs.interactive_trials.resume_turn", str(run_id), str(turn_id)
        )

    def _enqueue(self, function: str, *args: str) -> None:
        from redis import Redis
        from rq import Queue

        Queue(self.queue_name, connection=Redis.from_url(self.redis_url)).enqueue(
            function, *args, job_timeout=INTERACTIVE_TRIAL_JOB_TIMEOUT_SECONDS
        )
