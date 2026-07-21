from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from courtroom_domain import CaseFile
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_service.api.deps import (
    get_case_file_repository,
    get_simulation_queue,
    get_simulation_run_repository,
)
from api_service.main import create_app
from api_service.repositories.case_files import StoredCaseFile
from api_service.repositories.simulation_runs import StoredSimulationRun


class InMemoryCaseFileRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, StoredCaseFile] = {}

    def create(self, case_file: CaseFile, *, status: str = "draft") -> StoredCaseFile:
        record = StoredCaseFile(
            id=uuid4(),
            case_file=case_file,
            status=status,
            revision=1,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.records[record.id] = record
        return record

    def list(self) -> list[StoredCaseFile]:
        return sorted(
            self.records.values(),
            key=lambda record: (record.updated_at, record.created_at),
            reverse=True,
        )

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        return self.records.get(case_file_id)

    def replace_case_file(
        self,
        case_file_id: UUID,
        case_file: CaseFile,
        *,
        expected_revision: int,
        status: str | None = None,
    ) -> StoredCaseFile:
        record = self.records[case_file_id]
        updated = StoredCaseFile(
            id=record.id,
            case_file=case_file,
            status=status or record.status,
            revision=record.revision + 1,
            created_at=record.created_at,
            updated_at=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
        )
        self.records[case_file_id] = updated
        return updated


class InMemorySimulationRunRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, StoredSimulationRun] = {}

    def get(self, simulation_run_id: UUID) -> StoredSimulationRun | None:
        return self.records.get(simulation_run_id)

    def list_for_dashboard(self) -> list[StoredSimulationRun]:
        return sorted(
            [
                record
                for record in self.records.values()
                if record.status != "failed"
            ],
            key=lambda record: (record.created_at, record.completed_at or record.created_at),
            reverse=True,
        )

    def create_pending(self, case_file_id: UUID) -> StoredSimulationRun:
        for record in self.records.values():
            if record.case_file_id == case_file_id:
                raise RuntimeError("duplicate simulation")
        record = StoredSimulationRun(
            id=uuid4(),
            case_file_id=case_file_id,
            status="pending",
            result=None,
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=None,
            completed_at=None,
        )
        self.records[record.id] = record
        return record

    def mark_running(self, simulation_run_id: UUID) -> StoredSimulationRun:
        record = self.records[simulation_run_id]
        updated = StoredSimulationRun(
            id=record.id,
            case_file_id=record.case_file_id,
            status="running",
            result=record.result,
            audio_manifest=record.audio_manifest,
            audio_storage=record.audio_storage,
            error_message=None,
            created_at=record.created_at,
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=record.completed_at,
        )
        self.records[simulation_run_id] = updated
        return updated

    def store_result(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> StoredSimulationRun:
        record = self.records[simulation_run_id]
        updated = StoredSimulationRun(
            id=record.id,
            case_file_id=record.case_file_id,
            status="hearing_completed",
            result=result,
            audio_manifest=record.audio_manifest,
            audio_storage=record.audio_storage,
            error_message=None,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )
        self.records[simulation_run_id] = updated
        return updated

    def mark_generating_audio(self, simulation_run_id: UUID) -> StoredSimulationRun:
        record = self.records[simulation_run_id]
        updated = StoredSimulationRun(
            id=record.id,
            case_file_id=record.case_file_id,
            status="generating_audio",
            result=record.result,
            audio_manifest=record.audio_manifest,
            audio_storage=record.audio_storage,
            error_message=None,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )
        self.records[simulation_run_id] = updated
        return updated

    def store_audio_artifacts(
        self,
        simulation_run_id: UUID,
        audio_manifest: list[dict[str, object]],
        audio_storage: dict[str, object],
    ) -> StoredSimulationRun:
        record = self.records[simulation_run_id]
        updated = StoredSimulationRun(
            id=record.id,
            case_file_id=record.case_file_id,
            status=record.status,
            result=record.result,
            audio_manifest=audio_manifest,
            audio_storage=audio_storage,
            error_message=None,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )
        self.records[simulation_run_id] = updated
        return updated

    def mark_completed(
        self,
        simulation_run_id: UUID,
    ) -> StoredSimulationRun:
        record = self.records[simulation_run_id]
        updated = StoredSimulationRun(
            id=record.id,
            case_file_id=record.case_file_id,
            status="completed",
            result=record.result,
            audio_manifest=record.audio_manifest,
            audio_storage=record.audio_storage,
            error_message=None,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.records[simulation_run_id] = updated
        return updated

    def mark_failed(
        self,
        simulation_run_id: UUID,
        error_message: str,
    ) -> StoredSimulationRun:
        record = self.records[simulation_run_id]
        updated = StoredSimulationRun(
            id=record.id,
            case_file_id=record.case_file_id,
            status="failed",
            result=record.result,
            audio_manifest=record.audio_manifest,
            audio_storage=record.audio_storage,
            error_message=error_message,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.records[simulation_run_id] = updated
        return updated


class InMemorySimulationQueue:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.enqueued: list[tuple[UUID, UUID]] = []

    def enqueue_simulation(
        self,
        simulation_run_id: UUID,
        case_file_id: UUID,
    ) -> None:
        if self.fail:
            raise RuntimeError("queue unavailable")
        self.enqueued.append((simulation_run_id, case_file_id))


def build_client(
    *,
    case_file_repository: InMemoryCaseFileRepository | None = None,
    simulation_repository: InMemorySimulationRunRepository | None = None,
    simulation_queue: InMemorySimulationQueue | None = None,
) -> TestClient:
    app: FastAPI = create_app()
    if case_file_repository is not None:
        app.dependency_overrides[get_case_file_repository] = lambda: (
            case_file_repository
        )
    if simulation_repository is not None:
        app.dependency_overrides[get_simulation_run_repository] = lambda: (
            simulation_repository
        )
    if simulation_queue is not None:
        app.dependency_overrides[get_simulation_queue] = lambda: simulation_queue
    return TestClient(app)


class SimulationApiTest(unittest.TestCase):
    def test_start_simulation_creates_pending_run_and_enqueues_job(self) -> None:
        repository = InMemoryCaseFileRepository()
        simulation_repository = InMemorySimulationRunRepository()
        simulation_queue = InMemorySimulationQueue()
        client = build_client(
            case_file_repository=repository,
            simulation_repository=simulation_repository,
            simulation_queue=simulation_queue,
        )
        created_case_file = client.post("/case-files").json()

        response = client.post(
            "/start-simulation",
            json={"case_file_id": created_case_file["id"]},
        )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        simulation_run_id = UUID(payload["simulation_run_id"])
        case_file_id = UUID(created_case_file["id"])
        self.assertEqual(payload["case_file_id"], created_case_file["id"])
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(simulation_queue.enqueued, [(simulation_run_id, case_file_id)])
        self.assertEqual(
            simulation_repository.records[simulation_run_id].status, "pending"
        )
        self.assertEqual(repository.records[case_file_id].status, "simulation_started")

    def test_start_simulation_returns_404_for_unknown_case_file(self) -> None:
        client = build_client(
            case_file_repository=InMemoryCaseFileRepository(),
            simulation_repository=InMemorySimulationRunRepository(),
            simulation_queue=InMemorySimulationQueue(),
        )

        response = client.post(
            "/start-simulation",
            json={"case_file_id": "00000000-0000-0000-0000-000000000000"},
        )

        self.assertEqual(response.status_code, 404)

    def test_start_simulation_marks_run_failed_when_enqueue_fails(self) -> None:
        repository = InMemoryCaseFileRepository()
        simulation_repository = InMemorySimulationRunRepository()
        client = build_client(
            case_file_repository=repository,
            simulation_repository=simulation_repository,
            simulation_queue=InMemorySimulationQueue(fail=True),
        )
        created_case_file = client.post("/case-files").json()

        response = client.post(
            "/start-simulation",
            json={"case_file_id": created_case_file["id"]},
        )

        self.assertEqual(response.status_code, 503)
        run = next(iter(simulation_repository.records.values()))
        self.assertEqual(run.status, "failed")
        self.assertIn("Failed to enqueue simulation", run.error_message or "")

    def test_start_simulation_rejects_second_run_for_case_file(self) -> None:
        repository = InMemoryCaseFileRepository()
        simulation_repository = InMemorySimulationRunRepository()
        client = build_client(
            case_file_repository=repository,
            simulation_repository=simulation_repository,
            simulation_queue=InMemorySimulationQueue(),
        )
        created_case_file = client.post("/case-files").json()

        first_response = client.post(
            "/start-simulation",
            json={"case_file_id": created_case_file["id"]},
        )
        second_response = client.post(
            "/start-simulation",
            json={"case_file_id": created_case_file["id"]},
        )

        self.assertEqual(first_response.status_code, 202)
        self.assertEqual(second_response.status_code, 409)

    def test_list_simulation_runs_returns_running_and_completed_runs(self) -> None:
        case_file_repository = InMemoryCaseFileRepository()
        simulation_repository = InMemorySimulationRunRepository()
        client = build_client(
            case_file_repository=case_file_repository,
            simulation_repository=simulation_repository,
        )

        created_case_file = client.post("/case-files").json()
        case_file_id = UUID(created_case_file["id"])
        completed_run_id = uuid4()
        simulation_repository.records[completed_run_id] = StoredSimulationRun(
            id=completed_run_id,
            case_file_id=case_file_id,
            status="completed",
            result={
                "full_trial_transcript": [
                    {
                        "scene": "verdict",
                        "speaker_id": "judge",
                        "text": "[firm] Guilty.",
                    }
                ],
                "verdict": {"outcome": "guilty"},
            },
            audio_manifest=[
                {
                    "turnId": 1,
                    "speakerId": "judge",
                    "scene": "verdict",
                    "text": "[firm] Guilty.",
                    "cleanText": "Guilty.",
                    "emotion": "firm",
                    "audioUrl": "https://cdn.example/audio/1.wav",
                    "durationMs": 1800,
                    "subtitleChunks": [
                        {"text": "Guilty.", "startMs": 0, "endMs": 1800}
                    ],
                }
            ],
            audio_storage={"bucket": "audio"},
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        )
        incomplete_run_id = uuid4()
        simulation_repository.records[incomplete_run_id] = StoredSimulationRun(
            id=incomplete_run_id,
            case_file_id=case_file_id,
            status="running",
            result={"full_trial_transcript": []},
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 1, 0, 3, tzinfo=timezone.utc),
        )

        response = client.get("/simulation-runs")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["simulationRunId"], str(completed_run_id))
        self.assertEqual(payload[0]["caseFile"]["id"], created_case_file["id"])
        self.assertEqual(payload[0]["caseFile"]["charge"], "Grand theft auto")
        self.assertEqual(payload[0]["playback"]["turnCount"], 1)
        self.assertEqual(payload[0]["playback"]["durationMs"], 1800)
        self.assertEqual(payload[0]["playback"]["verdictLabel"], "guilty")
        self.assertEqual(payload[1]["simulationRunId"], str(incomplete_run_id))
        self.assertEqual(payload[1]["status"], "running")
        self.assertEqual(payload[1]["playback"]["turnCount"], 0)

    def test_get_simulation_playback_returns_sanitized_frontend_payload(self) -> None:
        case_file_repository = InMemoryCaseFileRepository()
        simulation_repository = InMemorySimulationRunRepository()
        client = build_client(
            case_file_repository=case_file_repository,
            simulation_repository=simulation_repository,
        )

        created_case_file = client.post("/case-files").json()
        case_file_id = UUID(created_case_file["id"])
        simulation_run_id = uuid4()
        simulation_repository.records[simulation_run_id] = StoredSimulationRun(
            id=simulation_run_id,
            case_file_id=case_file_id,
            status="completed",
            result={
                "full_trial_transcript": [
                    {
                        "scene": "opening",
                        "speaker_id": "prosecution",
                        "text": "[firm] Members of the jury.",
                    },
                    {
                        "scene": "verdict",
                        "speaker_id": "judge",
                        "text": "[measured] Guilty.",
                    },
                ],
                "node_telemetry": [{"node_name": "hidden"}],
                "verdict": {"outcome": "guilty"},
            },
            audio_manifest=[
                {
                    "turnId": 1,
                    "speakerId": "prosecution",
                    "scene": "opening",
                    "text": "[firm] Members of the jury.",
                    "cleanText": "Members of the jury.",
                    "emotion": "firm",
                    "audioUrl": "https://cdn.example/audio/1.wav",
                    "durationMs": 2100,
                    "subtitleChunks": [
                        {
                            "text": "Members of the jury.",
                            "startMs": 0,
                            "endMs": 2100,
                        }
                    ],
                }
            ],
            audio_storage={"turns": [{"key": "hidden"}]},
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        )

        response = client.get(f"/simulation-runs/{simulation_run_id}/playback")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["simulationRunId"], str(simulation_run_id))
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["transcript"]["case_metadata"]["charge"], "Grand theft auto")
        self.assertIn("judge", payload["transcript"]["voice_character_map"])
        self.assertEqual(payload["playbackManifest"][0]["cleanText"], "Members of the jury.")
        self.assertNotIn("audio_storage", payload)
        self.assertNotIn("node_telemetry", payload)

    def test_get_simulation_playback_returns_conflict_when_audio_is_missing(self) -> None:
        case_file_repository = InMemoryCaseFileRepository()
        simulation_repository = InMemorySimulationRunRepository()
        client = build_client(
            case_file_repository=case_file_repository,
            simulation_repository=simulation_repository,
        )

        created_case_file = client.post("/case-files").json()
        case_file_id = UUID(created_case_file["id"])
        simulation_run_id = uuid4()
        simulation_repository.records[simulation_run_id] = StoredSimulationRun(
            id=simulation_run_id,
            case_file_id=case_file_id,
            status="hearing_completed",
            result={"full_trial_transcript": []},
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=None,
        )

        response = client.get(f"/simulation-runs/{simulation_run_id}/playback")

        self.assertEqual(response.status_code, 409)
