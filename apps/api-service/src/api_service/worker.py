from __future__ import annotations

import argparse
import platform

from redis import Redis
from rq import SimpleWorker, Worker

from .workflows.simulation_pipeline import _load_agent_service_contract


def _worker_class() -> type[Worker]:
    # macOS RQ work horses fork per job, which is not reliable once the agent stack
    # has initialized Objective-C-backed libraries. SimpleWorker runs jobs inline.
    if platform.system() == "Darwin":
        return SimpleWorker
    return Worker


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an RQ worker for api-service.")
    parser.add_argument("queues", nargs="+", help="Queue names to consume.")
    parser.add_argument(
        "--url",
        default="redis://localhost:6379/0",
        help="Redis connection URL.",
    )
    args = parser.parse_args()

    _load_agent_service_contract()

    redis_connection = Redis.from_url(args.url)
    worker = _worker_class()(args.queues, connection=redis_connection)
    worker.work()


if __name__ == "__main__":
    main()
