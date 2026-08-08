"""RQ entry points for durable interactive trial execution."""

from __future__ import annotations

import base64
import importlib
from uuid import UUID

from ..core.config import (
    get_database_url,
    get_r2_access_key_id,
    get_r2_bucket_name,
    get_r2_endpoint_url,
    get_r2_public_base_url,
    get_r2_region,
    get_r2_secret_access_key,
)
from ..repositories.case_files import PostgresCaseFileRepository
from ..repositories.interactive_trial_runs import PostgresInteractiveTrialRunRepository
from ..services.storage import R2ObjectStorageService


def run_initial(run_id: str) -> None:
    runs = PostgresInteractiveTrialRunRepository(get_database_url())
    case_files = PostgresCaseFileRepository(get_database_url())
    identifier = UUID(run_id)
    run = runs.get(identifier)
    if run is None or run.status in {"completed", "failed", "awaiting_human"}:
        return
    try:
        runs.mark_running(identifier)
        case_file = case_files.get(run.case_file_id)
        if case_file is None:
            raise RuntimeError("Case file no longer exists")
        result = _execute(
            thread_id=run.langgraph_thread_id,
            case_file=case_file.case_file,
            human_attorney_side=run.human_attorney_side,
            human_witness_plan=run.human_witness_plan,
        )
        runs.store_progress(
            identifier, state_snapshot=result.state, interrupt=result.interrupt
        )
    except Exception:
        runs.mark_failed(
            identifier, "Interactive trial execution failed. Please start a new run."
        )
        raise


def resume_turn(run_id: str, turn_id: str) -> None:
    runs = PostgresInteractiveTrialRunRepository(get_database_url())
    identifier, turn_identifier = UUID(run_id), UUID(turn_id)
    run = runs.get(identifier)
    turn = runs.get_turn(turn_identifier)
    if run is None or turn is None or run.pending_turn_id != turn_identifier:
        return
    if turn.status == "consumed":
        return
    try:
        runs.mark_running(identifier, turn_id=turn_identifier)
        resume_payload = {"object": bool(turn.object_requested)}
        if turn.is_final is not None:
            resume_payload["is_final"] = turn.is_final
        if turn.object_requested:
            if not turn.object_key or not turn.content_type:
                raise RuntimeError(
                    "Participant objection recording is missing storage metadata"
                )
            audio = _storage().download_private_bytes(key=turn.object_key)
            resume_payload.update(
                {
                    "audio_base64": base64.b64encode(audio).decode("ascii"),
                    "mime_type": turn.content_type,
                }
            )
        result = _execute(
            thread_id=run.langgraph_thread_id,
            resume_payload=resume_payload,
        )
        runs.store_progress(
            identifier,
            state_snapshot=result.state,
            interrupt=result.interrupt,
            consumed_turn_id=turn_identifier,
        )
    except Exception:
        runs.mark_failed(
            identifier,
            "Participant response could not be processed. Please start a new run.",
        )
        raise


def _execute(**kwargs: object):
    from ..workflows.simulation_pipeline import _load_agent_service_contract

    run_trial, _ = _load_agent_service_contract()
    package_name = run_trial.__module__.removesuffix(".service")
    interactive_service = importlib.import_module(f"{package_name}.interactive.service")

    with interactive_service.build_interactive_postgres_checkpointer(
        get_database_url()
    ) as checkpointer:
        return interactive_service.execute_interactive_trial(
            checkpointer=checkpointer, **kwargs
        )


def _storage() -> R2ObjectStorageService:
    return R2ObjectStorageService(
        bucket_name=get_r2_bucket_name(),
        endpoint_url=get_r2_endpoint_url(),
        access_key_id=get_r2_access_key_id(),
        secret_access_key=get_r2_secret_access_key(),
        public_base_url=get_r2_public_base_url(),
        region_name=get_r2_region(),
    )
