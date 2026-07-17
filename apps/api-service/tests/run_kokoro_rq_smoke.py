from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import text


REPO_ROOT = Path(__file__).resolve().parents[3]
API_SERVICE_SRC = REPO_ROOT / "apps" / "api-service" / "src"
PYTHON_DOMAIN_SRC = REPO_ROOT / "packages" / "python-domain" / "src"

for import_path in (API_SERVICE_SRC, PYTHON_DOMAIN_SRC):
    path_str = str(import_path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from api_service.core.config import get_database_url, get_redis_url
from api_service.db.session import get_session_factory
from api_service.repositories.simulation_runs import PostgresSimulationRunRepository


CASE_FILE_ID = "889a9e00-cde0-4fc8-aa97-3eed585ec2ea"
SIMULATION_RESULT: dict[str, Any] | None = {
    "run": {
        "run_id": "10f728cf-6d14-41e9-8741-8c79e640326d",
        "case_id": "540f88e7-7130-4f8c-9f66-ab62a7bcd4a9",
        "model_name": "gpt-5-mini",
        "started_at": "2026-07-16T13:56:49.370298+00:00",
        "duration_ms": 184798,
        "environment": "local",
        "completed_at": "2026-07-16T13:59:54.169165+00:00",
        "graph_version": "v1",
        "prompt_version": "v1",
        "judge_model_name": "gpt-5-nano",
        "langsmith_trace_id": "019f6b37-3a77-7fd1-a6f7-bc90a902a4e5",
        "deterministic_validation_passed": True,
    },
    "full_trial_transcript": [
        {
            "text": "Members of the jury, [steady] you will see repair-lot security footage showing Jordan Vale driving the vehicle out of the lot at 8:42 p.m. [measured] You will also see text messages between Jordan Vale and repair-lot personnel asking when the vehicle should be returned [firm]. W1 will testify about the conversations and the question of whether the repair lot gave implied permission to move the vehicle [somber]. The evidence will allow you to decide the disputed issue of whether Jordan Vale intended to permanently deprive the owner of the vehicle [quiet].",
            "scene": "opening",
            "ruling": None,
            "speaker_id": "prosecution",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "Members of the jury, [steady] you'll see the same footage and texts the prosecutor mentioned, but you will also hear that Mr. Vale asked when the car should be returned before he moved it. [measured] The evidence will show the repair lot gave implied permission and that Mr. Vale had no intent to permanently deprive the owner. [firm] At the end of this trial we will ask you to find him not guilty because the People cannot prove intent beyond a reasonable doubt. [quiet]",
            "scene": "opening",
            "ruling": None,
            "speaker_id": "defense",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "[steady] When you discovered the vehicle was missing, did you find any written or verbal authorization from the repair lot allowing anyone to remove that vehicle?",
            "scene": "direct",
            "ruling": None,
            "speaker_id": "prosecution",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "[steady] No, I did not find any written authorization in the vehicle's file. [measured] No one on staff reported giving verbal permission for the vehicle to be removed.",
            "scene": "direct",
            "ruling": None,
            "speaker_id": "W1",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "[pressing] Does the repair lot keep a keys-out log, and does that log show any employee signing out the keys to this vehicle at or around 8:42 PM when the security footage shows it leaving?",
            "scene": "cross",
            "ruling": None,
            "speaker_id": "defense",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "[firm] Objection, hearsay. Calls for the contents of an out-of-court record (the keys-out log) to prove its entries without foundation/authentication or establishment of the business-records exception; hearsay objection warranted.",
            "scene": "objection",
            "ruling": None,
            "speaker_id": "prosecution",
            "objection_type": "hearsay",
            "cited_chunk_ids": None,
        },
        {
            "text": "[firm] The question seeks the contents of an out-of-court log to prove its entries without any authentication or foundation for a business-records exception. [calm] Absent testimony establishing the log’s existence, its creation in the ordinary course, time of entry, and the person with knowledge, the log is hearsay. [measured] The objection is sustained; the proponent may lay proper foundation for admissibility under the business-records exception or authenticate the log before asking for its contents.",
            "scene": "ruling",
            "ruling": "sustained",
            "speaker_id": "judge",
            "objection_type": None,
            "cited_chunk_ids": [],
        },
        {
            "text": "Mr. Vale, [measured] can you explain why you moved the vehicle from the repair lot and why you returned it later?",
            "scene": "direct",
            "ruling": None,
            "speaker_id": "defense",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "I moved the vehicle because I needed to retrieve personal belongings and I believed the lot had given me permission to move it [measured]. I returned it later as soon as I realized they wanted it back and to avoid any dispute [steady].",
            "scene": "direct",
            "ruling": None,
            "speaker_id": "W2",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "Mr. Vale, did any employee or agent of the repair lot expressly tell you—either in person or by text—that you had permission to take the vehicle at or before 8:42 PM on the night it left their lot? [pressing]",
            "scene": "cross",
            "ruling": None,
            "speaker_id": "prosecution",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "[firm] Objection, hearsay. Objection — hearsay. The question asks the witness to relate an out-of-court statement by a repair-lot employee/agent offered to prove that he had permission; no hearsay exception or foundation for admissibility has been established.",
            "scene": "objection",
            "ruling": None,
            "speaker_id": "defense",
            "objection_type": "hearsay",
            "cited_chunk_ids": None,
        },
        {
            "text": "[firm] The question asks the witness to relay an out-of-court statement by a repair-lot employee/agent to prove permission. Absent a foundation showing the declarant was acting within the scope of employment and that the statement qualifies as a party-admission or other exception, this is hearsay and inadmissible as framed.",
            "scene": "ruling",
            "ruling": "sustained",
            "speaker_id": "judge",
            "objection_type": None,
            "cited_chunk_ids": [],
        },
        {
            "text": "[firm] The security footage clearly shows Jordan Vale driving the vehicle out of the repair lot at 8:42 p.m., and the lot witness testified there was no written authorization and no staff reported giving verbal permission. [measured] The text messages on the record show Vale asking when the vehicle should be returned, a communication consistent with someone who knew the car was not theirs and with no evidence of consent to remove it. [steady] Vale admits he moved the car and only returned it after he realized the lot wanted it back, but that admission does not erase the fact the removal was unauthorized and the jury may reasonably infer intent from those facts. [somber] Based on the footage, the lot’s testimony that no permission was given, and the defendant’s own communications and conduct, I ask you to find Jordan Vale guilty beyond a reasonable doubt.",
            "scene": "closing",
            "ruling": None,
            "speaker_id": "prosecution",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "[steady] The footage shows Mr. Vale driving the car, but footage alone does not prove he intended to permanently deprive anyone of their property. [measured] The texts on the record asking when the vehicle should be returned, together with Mr. Vale’s testimony that he moved the car only to retrieve personal items and then returned it, are consistent with lack of intent to steal. [firm] The People could not authenticate the keys-out log or introduce employees’ out-of-court statements, so they have not overcome the reasonable doubt created by those admitted facts and testimony. [quiet] Given the evidence admitted at trial, you must find there is reasonable doubt about guilt and return a verdict of not guilty.",
            "scene": "closing",
            "ruling": None,
            "speaker_id": "defense",
            "objection_type": None,
            "cited_chunk_ids": None,
        },
        {
            "text": "Not guilty, [somber], because while E1 shows the vehicle leaving the repair lot at 8:42 p.m., the People did not prove beyond a reasonable doubt that Vale intended to permanently deprive the owner. Not guilty, [measured], because W2 testified he moved the vehicle to retrieve personal belongings and believed he had permission, and E2 shows he asked when the vehicle should be returned. Not guilty, [firm], because W1 testified no written authorization existed and no staff reported verbal permission, undermining any claim of express permission. Not guilty, [quiet], because the People have not authenticated crucial records or proven the mens rea required for grand theft auto beyond a reasonable doubt.",
            "scene": "verdict",
            "ruling": None,
            "speaker_id": "judge",
            "objection_type": None,
            "cited_chunk_ids": ["E1", "E2", "W1", "W2"],
        },
    ],
}

TTS_QUEUE_NAME = "simulation_tts"
POLL_INTERVAL_SECONDS = 2.0
POLL_TIMEOUT_SECONDS = 300.0


def main() -> None:
    case_file_id = _parse_case_file_id(CASE_FILE_ID)
    simulation_result = _parse_simulation_result(SIMULATION_RESULT)

    database_url = get_database_url()
    redis_url = get_redis_url()
    _assert_audio_stage_schema(database_url)
    runs = PostgresSimulationRunRepository(database_url)

    run = runs.create_pending(case_file_id)
    print(f"Created simulation run: {run.id}")
    print(f"Case file id: {case_file_id}")

    seeded_run = runs.store_result(run.id, simulation_result)
    print(f"Seeded placeholder result. Current status: {seeded_run.status}")

    job = _enqueue_tts_job(str(run.id), redis_url)
    print(f"Enqueued RQ job: {job.id}")
    print(f"Queue: {TTS_QUEUE_NAME}")

    final_run = _wait_for_completion(
        run_id=run.id,
        runs=runs,
        redis_url=redis_url,
        job_id=job.id,
    )

    print("Final simulation run state:")
    print(json.dumps(_run_summary(final_run), indent=2, default=str))

    if final_run.status != "completed":
        raise RuntimeError(
            f"Audio stage did not complete successfully. Final status: {final_run.status}"
        )


def _parse_case_file_id(raw_value: str) -> UUID:
    if raw_value == "REPLACE_WITH_CASE_FILE_UUID":
        raise RuntimeError(
            "Replace CASE_FILE_ID with a real case_files.id value before running this script."
        )
    return UUID(raw_value)


def _parse_simulation_result(
    result: dict[str, Any] | None,
) -> dict[str, Any]:
    if result is None:
        raise RuntimeError(
            "Replace SIMULATION_RESULT with the LLM result payload before running this script."
        )

    if not isinstance(result, dict):
        raise RuntimeError("SIMULATION_RESULT must be a Python dict.")

    if not result.get("audio_script_timeline") and not result.get(
        "full_trial_transcript"
    ):
        raise RuntimeError(
            "SIMULATION_RESULT must include audio_script_timeline or full_trial_transcript."
        )

    return result


def _enqueue_tts_job(simulation_run_id: str, redis_url: str):
    from redis import Redis
    from rq import Queue

    redis_connection = Redis.from_url(redis_url)
    queue = Queue(TTS_QUEUE_NAME, connection=redis_connection)
    return queue.enqueue(
        "api_service.jobs.simulations.generate_audio_stage",
        simulation_run_id,
    )


def _assert_audio_stage_schema(database_url: str) -> None:
    session_factory = get_session_factory(database_url)
    with session_factory() as session:
        column_result = session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'simulation_runs'
                  AND column_name IN ('audio_manifest', 'audio_storage')
                """
            )
        )
        columns = {row[0] for row in column_result}

        constraint_result = session.execute(
            text(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conname = 'chk_simulation_runs_status'
                """
            )
        )
        constraint_definition = constraint_result.scalar_one_or_none()

    missing = {"audio_manifest", "audio_storage"} - columns
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise RuntimeError(
            "simulation_runs is missing required audio-stage columns: "
            f"{missing_list}. Apply infra/db/migrations/003_add_simulation_audio_stage.sql "
            "to this database, then rerun the script."
        )

    if constraint_definition is None or "hearing_completed" not in constraint_definition:
        raise RuntimeError(
            "simulation_runs status constraint does not allow 'hearing_completed'. "
            "Apply infra/db/migrations/004_allow_hearing_completed_status.sql "
            "to this database, then rerun the script."
        )


def _wait_for_completion(
    *,
    run_id: UUID,
    runs: PostgresSimulationRunRepository,
    redis_url: str,
    job_id: str,
):
    from redis import Redis
    from rq.job import Job

    redis_connection = Redis.from_url(redis_url)
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        run = runs.get(run_id)
        job = Job.fetch(job_id, connection=redis_connection)

        status = run.status if run is not None else "missing"
        print(f"Polling: run_status={status} rq_status={job.get_status()}")

        if run is None:
            raise RuntimeError(f"Simulation run disappeared: {run_id}")

        if run.status == "completed":
            return run

        if run.status == "failed":
            raise RuntimeError(
                f"Audio stage failed: {run.error_message or 'unknown error'}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)

    latest_run = runs.get(run_id)
    raise RuntimeError(
        "Timed out waiting for the simulation_tts worker to finish. "
        f"Latest run status: {latest_run.status if latest_run else 'missing'}"
    )


def _run_summary(run) -> dict[str, Any]:
    return {
        "id": str(run.id),
        "case_file_id": str(run.case_file_id),
        "status": run.status,
        "error_message": run.error_message,
        "audio_manifest_count": len(run.audio_manifest or []),
        "audio_storage": run.audio_storage,
        "completed_at": run.completed_at,
    }


if __name__ == "__main__":
    main()
