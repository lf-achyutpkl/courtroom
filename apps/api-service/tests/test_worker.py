from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from api_service.worker import _worker_class, main


class WorkerEntrypointTest(unittest.TestCase):
    @patch("api_service.worker.platform.system", return_value="Darwin")
    def test_worker_class_uses_simple_worker_on_macos(self, _: MagicMock) -> None:
        from rq import SimpleWorker

        self.assertIs(_worker_class(), SimpleWorker)

    @patch("api_service.worker.platform.system", return_value="Linux")
    def test_worker_class_uses_standard_worker_off_macos(
        self,
        _: MagicMock,
    ) -> None:
        from rq import Worker

        self.assertIs(_worker_class(), Worker)

    @patch("api_service.worker._worker_class")
    @patch("api_service.worker.Redis.from_url")
    @patch("api_service.worker._load_agent_service_contract")
    @patch("sys.argv", ["api_service.worker", "--url", "redis://example/0", "q1", "q2"])
    def test_main_preloads_contract_and_starts_worker(
        self,
        load_contract: MagicMock,
        redis_from_url: MagicMock,
        worker_class: MagicMock,
    ) -> None:
        worker_instance = MagicMock()
        worker_ctor = MagicMock(return_value=worker_instance)
        worker_class.return_value = worker_ctor
        redis_connection = object()
        redis_from_url.return_value = redis_connection

        main()

        load_contract.assert_called_once_with()
        redis_from_url.assert_called_once_with("redis://example/0")
        worker_ctor.assert_called_once_with(
            ["q1", "q2"],
            connection=redis_connection,
        )
        worker_instance.work.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
