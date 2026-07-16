from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

from courtroom_domain import CaseFile

from worker_service.jobs.completion import apply_completion
from worker_service.models.completions import SimulationCompletion
from worker_service.models.jobs import SimulationJob
from worker_service.main import run_simulation


class InMemoryCaseFiles:
    def __init__(self, case_file: CaseFile | None) -> None:
        self.case_file = case_file

    def get(self, case_file_id: UUID) -> CaseFile | None:
        return self.case_file


class InMemoryRuns:
    def __init__(self) -> None:
        self.running: list[UUID] = []
        self.completed: list[tuple[UUID, dict[str, object]]] = []
        self.failed: list[tuple[UUID, str]] = []

    def mark_running(self, simulation_run_id: UUID) -> None:
        self.running.append(simulation_run_id)

    def mark_completed(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> None:
        self.completed.append((simulation_run_id, result))

    def mark_failed(self, simulation_run_id: UUID, error_message: str) -> None:
        self.failed.append((simulation_run_id, error_message))


class InMemoryCompletionQueue:
    def __init__(self) -> None:
        self.messages: list[SimulationCompletion] = []

    def enqueue_completion(self, completion: SimulationCompletion) -> None:
        self.messages.append(completion)


class FailingCompletionQueue:
    def __init__(self) -> None:
        self.messages: list[SimulationCompletion] = []

    def enqueue_completion(self, completion: SimulationCompletion) -> None:
        self.messages.append(completion)
        raise RuntimeError("publish failed")


def build_case_file() -> CaseFile:
    return CaseFile.model_validate(
        {
            "case_id": str(uuid4()),
            "case_type": "criminal",
            "charge_or_claim": "Grand theft auto",
            "parties": {
                "plaintiff_or_prosecution": "People of California",
                "defendant": "Alex Rivera",
            },
            "ground_truth": "The defendant took a parked vehicle.",
            "evidence": [],
            "witnesses": [],
        }
    )


class WorkerServiceTest(unittest.TestCase):
    def test_run_simulation_publishes_completed_result(self) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        completions = InMemoryCompletionQueue()

        with patch(
            "worker_service.services.simulation_runner._run_trial",
            return_value={"run": {"run_id": "trial-1"}},
        ):
            run_simulation(
                SimulationJob(
                    simulation_run_id=simulation_run_id,
                    case_file_id=case_file_id,
                ),
                case_files=InMemoryCaseFiles(build_case_file()),
                runs=runs,
                completions=completions,
            )

        self.assertEqual(runs.running, [simulation_run_id])
        self.assertEqual(len(completions.messages), 1)
        self.assertEqual(completions.messages[0].status, "completed")
        self.assertEqual(completions.messages[0].result, {"run": {"run_id": "trial-1"}})

    def test_run_simulation_does_not_publish_failed_when_completed_publish_fails(
        self,
    ) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        completions = FailingCompletionQueue()

        with patch(
            "worker_service.services.simulation_runner._run_trial",
            return_value={"run": {"run_id": "trial-1"}},
        ):
            with self.assertRaisesRegex(RuntimeError, "publish failed"):
                run_simulation(
                    SimulationJob(
                        simulation_run_id=simulation_run_id,
                        case_file_id=case_file_id,
                    ),
                    case_files=InMemoryCaseFiles(build_case_file()),
                    runs=InMemoryRuns(),
                    completions=completions,
                )

        self.assertEqual(len(completions.messages), 1)
        self.assertEqual(completions.messages[0].status, "completed")

    def test_run_simulation_publishes_failed_result(self) -> None:
        simulation_run_id = uuid4()
        completions = InMemoryCompletionQueue()

        run_simulation(
            SimulationJob(
                simulation_run_id=simulation_run_id,
                case_file_id=uuid4(),
            ),
            case_files=InMemoryCaseFiles(None),
            runs=InMemoryRuns(),
            completions=completions,
        )

        self.assertEqual(len(completions.messages), 1)
        self.assertEqual(completions.messages[0].status, "failed")
        self.assertIn("Case file not found", completions.messages[0].error_message or "")

    def test_apply_completion_marks_completed(self) -> None:
        simulation_run_id = uuid4()
        runs = InMemoryRuns()

        apply_completion(
            SimulationCompletion(
                simulation_run_id=simulation_run_id,
                status="completed",
                result={"ok": True},
            ),
            runs=runs,
        )

        self.assertEqual(runs.completed, [(simulation_run_id, {"ok": True})])

    def test_apply_completion_marks_failed(self) -> None:
        simulation_run_id = uuid4()
        runs = InMemoryRuns()

        apply_completion(
            SimulationCompletion(
                simulation_run_id=simulation_run_id,
                status="failed",
                error_message="boom",
            ),
            runs=runs,
        )

        self.assertEqual(runs.failed, [(simulation_run_id, "boom")])


if __name__ == "__main__":
    unittest.main()
