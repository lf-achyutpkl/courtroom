from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from courtroom_domain import CaseFile

from api_service.queue.simulation_pipeline import (
    RUN_TRIAL_JOB_TIMEOUT_SECONDS,
    RqSimulationQueue,
)
from api_service.repositories.case_files import StoredCaseFile
from api_service.repositories.simulation_runs import StoredSimulationRun
from api_service.services.tts.service import SimulationAudioService
from api_service.workflows.simulation_pipeline import (
    SimulationGenerationJob,
    execute_audio_generation_stage,
    execute_generation_stage,
)


class InMemoryCaseFiles:
    def __init__(self, case_file: CaseFile | None) -> None:
        self.case_file = case_file

    def create(self, case_file: CaseFile) -> StoredCaseFile:
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return StoredCaseFile(
            id=uuid4(),
            case_file=case_file,
            status="draft",
            revision=1,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        if self.case_file is None:
            return None

        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return StoredCaseFile(
            id=case_file_id,
            case_file=self.case_file,
            status="draft",
            revision=1,
            created_at=timestamp,
            updated_at=timestamp,
        )


class InMemoryRuns:
    def __init__(self) -> None:
        self.records: dict[UUID, StoredSimulationRun] = {}
        self.running: list[UUID] = []
        self.generating_audio: list[UUID] = []
        self.completed: list[UUID] = []
        self.failed: list[tuple[UUID, str]] = []
        self.stored_results: list[tuple[UUID, dict[str, object]]] = []
        self.stored_audio_artifacts: list[
            tuple[UUID, list[dict[str, object]], dict[str, object]]
        ] = []

    def get(self, simulation_run_id: UUID) -> StoredSimulationRun | None:
        return self.records.get(simulation_run_id)

    def create_pending(self, case_file_id: UUID) -> StoredSimulationRun:
        simulation_run_id = uuid4()
        record = build_pending_run(simulation_run_id, case_file_id)
        self.records[simulation_run_id] = record
        return record

    def mark_running(self, simulation_run_id: UUID) -> StoredSimulationRun:
        self.running.append(simulation_run_id)
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
        self.stored_results.append((simulation_run_id, result))
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
        self.generating_audio.append(simulation_run_id)
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
        self.stored_audio_artifacts.append(
            (simulation_run_id, audio_manifest, audio_storage)
        )
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
        self.completed.append(simulation_run_id)
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
        self.failed.append((simulation_run_id, error_message))
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


def build_case_file() -> CaseFile:
    return CaseFile.model_validate(
        {
            "case_id": str(uuid4()),
            "case_title": "People v. Rivera",
            "case_type": "criminal",
            "charge_or_claim": "Grand theft auto",
            "parties": {
                "plaintiff_or_prosecution": "People of California",
                "defendant": "Alex Rivera",
            },
            "ground_truth": "The defendant took a parked vehicle.",
            "disputed_facts": [],
            "evidence": [],
            "witnesses": [],
        }
    )


def build_pending_run(
    simulation_run_id: UUID, case_file_id: UUID
) -> StoredSimulationRun:
    return StoredSimulationRun(
        id=simulation_run_id,
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


class SimulationPipelineTest(unittest.TestCase):
    def build_audio_service(self) -> SimulationAudioService:
        audio_service = MagicMock(spec=SimulationAudioService)
        audio_service.generate_for_run.return_value = (
            [
                {
                    "turnId": 1,
                    "speakerId": "judge",
                    "scene": "verdict",
                    "text": "Rendered speech.",
                    "cleanText": "Rendered speech.",
                    "emotion": None,
                    "audioUrl": "https://cdn.example/run/1.wav",
                    "durationMs": 1500,
                    "subtitleChunks": [
                        {"text": "Rendered speech.", "startMs": 0, "endMs": 1500}
                    ],
                }
            ],
            {
                "provider": "r2",
                "turns": [
                    {
                        "turnId": 1,
                        "speakerId": "judge",
                        "bucket": "courtroom-audio",
                        "key": "simulation-runs/run-1/audio/1.wav",
                        "url": "https://cdn.example/run/1.wav",
                        "contentType": "audio/wav",
                        "sizeBytes": 1024,
                        "voice": "af_sarah",
                        "stylePreset": "measured",
                    }
                ],
            },
        )
        return audio_service

    def test_generation_stage_marks_running_and_stores_result(self) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        runs.records[simulation_run_id] = build_pending_run(
            simulation_run_id,
            case_file_id,
        )

        with patch(
            "api_service.workflows.simulation_pipeline._run_trial",
            return_value={"run": {"run_id": "trial-1"}},
        ):
            execute_generation_stage(
                SimulationGenerationJob(
                    simulation_run_id=simulation_run_id,
                    case_file_id=case_file_id,
                ),
                case_files=InMemoryCaseFiles(build_case_file()),
                runs=runs,
            )

        self.assertEqual(runs.running, [simulation_run_id])
        self.assertEqual(
            runs.stored_results,
            [(simulation_run_id, {"run": {"run_id": "trial-1"}})],
        )
        self.assertEqual(
            runs.records[simulation_run_id].status,
            "hearing_completed",
        )

    def test_generation_stage_marks_failed_when_case_file_is_missing(self) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        runs.records[simulation_run_id] = build_pending_run(
            simulation_run_id,
            case_file_id,
        )

        with self.assertRaisesRegex(RuntimeError, "Case file not found"):
            execute_generation_stage(
                SimulationGenerationJob(
                    simulation_run_id=simulation_run_id,
                    case_file_id=case_file_id,
                ),
                case_files=InMemoryCaseFiles(None),
                runs=runs,
            )

        self.assertEqual(len(runs.failed), 1)
        self.assertIn("Case file not found", runs.failed[0][1])

    def test_audio_generation_stage_marks_generating_audio_before_synthesis(
        self,
    ) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        runs.records[simulation_run_id] = StoredSimulationRun(
            id=simulation_run_id,
            case_file_id=case_file_id,
            status="hearing_completed",
            result={"run": {"run_id": "trial-1"}},
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=None,
        )

        execute_audio_generation_stage(
            simulation_run_id,
            case_files=InMemoryCaseFiles(build_case_file()),
            runs=runs,
            audio_service=self.build_audio_service(),
        )

        self.assertEqual(runs.generating_audio, [simulation_run_id])

    def test_audio_generation_stage_stores_artifacts_and_completes(self) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        runs.records[simulation_run_id] = StoredSimulationRun(
            id=simulation_run_id,
            case_file_id=case_file_id,
            status="generating_audio",
            result={
                "full_trial_transcript": [
                    {
                        "scene": "verdict",
                        "speaker_id": "judge",
                        "text": "Rendered speech.",
                    }
                ]
            },
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=None,
        )

        execute_audio_generation_stage(
            simulation_run_id,
            case_files=InMemoryCaseFiles(build_case_file()),
            runs=runs,
            audio_service=self.build_audio_service(),
        )

        self.assertEqual(len(runs.stored_audio_artifacts), 1)
        self.assertEqual(runs.completed, [simulation_run_id])

    def test_audio_generation_stage_marks_failed_when_result_is_missing(self) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        runs.records[simulation_run_id] = StoredSimulationRun(
            id=simulation_run_id,
            case_file_id=case_file_id,
            status="generating_audio",
            result=None,
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=None,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "has no generated result for audio synthesis",
        ):
            execute_audio_generation_stage(
                simulation_run_id,
                case_files=InMemoryCaseFiles(build_case_file()),
                runs=runs,
                audio_service=self.build_audio_service(),
            )

        self.assertEqual(len(runs.failed), 1)

    def test_audio_generation_stage_marks_failed_when_case_file_is_missing(
        self,
    ) -> None:
        simulation_run_id = uuid4()
        case_file_id = uuid4()
        runs = InMemoryRuns()
        runs.records[simulation_run_id] = StoredSimulationRun(
            id=simulation_run_id,
            case_file_id=case_file_id,
            status="generating_audio",
            result={
                "full_trial_transcript": [
                    {
                        "scene": "verdict",
                        "speaker_id": "judge",
                        "text": "Rendered speech.",
                    }
                ]
            },
            audio_manifest=None,
            audio_storage=None,
            error_message=None,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=None,
        )

        with self.assertRaisesRegex(RuntimeError, "Case file not found"):
            execute_audio_generation_stage(
                simulation_run_id,
                case_files=InMemoryCaseFiles(None),
                runs=runs,
                audio_service=self.build_audio_service(),
            )

        self.assertEqual(len(runs.failed), 1)

    @patch("redis.Redis.from_url")
    @patch("rq.Queue")
    def test_queue_adapter_enqueues_dependent_jobs(
        self,
        queue_cls: MagicMock,
        redis_from_url: MagicMock,
    ) -> None:
        redis_connection = object()
        redis_from_url.return_value = redis_connection
        llm_queue = MagicMock()
        tts_queue = MagicMock()
        generation_job = MagicMock()
        generation_job.delete = MagicMock()
        llm_queue.enqueue.return_value = generation_job
        queue_cls.side_effect = [llm_queue, tts_queue]

        queue = RqSimulationQueue("redis://localhost:6379/0")
        simulation_run_id = uuid4()
        case_file_id = uuid4()

        queue.enqueue_simulation(simulation_run_id, case_file_id)

        llm_queue.enqueue.assert_called_once_with(
            "api_service.jobs.simulations.run_generation_stage",
            str(simulation_run_id),
            str(case_file_id),
            job_timeout=RUN_TRIAL_JOB_TIMEOUT_SECONDS,
        )
        tts_queue.enqueue.assert_called_once_with(
            "api_service.jobs.simulations.generate_audio_stage",
            str(simulation_run_id),
            depends_on=generation_job,
        )


if __name__ == "__main__":
    unittest.main()
