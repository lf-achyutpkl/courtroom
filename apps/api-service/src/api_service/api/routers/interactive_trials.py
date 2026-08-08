from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...api.deps import (
    get_case_file_repository,
    get_interactive_trial_queue,
    get_interactive_trial_repository,
    get_object_storage,
)
from ...core.config import (
    get_interactive_recording_max_bytes,
    get_interactive_recording_mime_types,
    get_interactive_upload_expiry_seconds,
)
from ...presenters.interactive_trials import build_interactive_trial_response
from ...queue.interactive_trial import InteractiveTrialQueue
from ...repositories.case_files import CaseFileRepository
from ...repositories.interactive_trial_runs import (
    InteractiveTrialStateError,
    PostgresInteractiveTrialRunRepository,
)
from ...schemas.interactive_trials import (
    CreateInteractiveTrialRunRequest,
    InteractiveTrialRunResponse,
    SubmitParticipantTurnRequest,
    SubmitParticipantTurnResponse,
    UploadAuthorizationRequest,
    UploadAuthorizationResponse,
)
from ...services.storage import ObjectStorageService

router = APIRouter(prefix="/interactive-trial-runs", tags=["interactive-trials"])


@router.post(
    "", response_model=InteractiveTrialRunResponse, status_code=status.HTTP_202_ACCEPTED
)
def create_interactive_trial_run(
    request: CreateInteractiveTrialRunRequest,
    case_files: CaseFileRepository = Depends(get_case_file_repository),
    runs: PostgresInteractiveTrialRunRepository = Depends(
        get_interactive_trial_repository
    ),
    queue: InteractiveTrialQueue = Depends(get_interactive_trial_queue),
) -> InteractiveTrialRunResponse:
    case_file = case_files.get(request.case_file_id)
    if case_file is None:
        raise HTTPException(status_code=404, detail="Case file not found.")
    eligible_ids = {
        witness.witness_id
        for witness in case_file.case_file.witnesses
        if witness.called_by == request.human_attorney_side
    }
    plan = request.human_witness_plan
    if len(plan) != len(set(plan)) or any(
        witness_id not in eligible_ids for witness_id in plan
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "humanWitnessPlan must contain unique witnesses assigned "
                "to the selected side."
            ),
        )
    run = runs.create(request.case_file_id, request.human_attorney_side, plan)
    try:
        queue.enqueue_initial(run.id)
    except Exception as exc:
        runs.mark_failed(run.id, "Unable to queue interactive trial execution.")
        raise HTTPException(
            status_code=503, detail="Unable to start interactive trial."
        ) from exc
    return build_interactive_trial_response(run, None)


@router.get("/{run_id}", response_model=InteractiveTrialRunResponse)
def get_interactive_trial_run(
    run_id: UUID,
    runs: PostgresInteractiveTrialRunRepository = Depends(
        get_interactive_trial_repository
    ),
) -> InteractiveTrialRunResponse:
    run = runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Interactive trial run not found.")
    turn = runs.get_turn(run.pending_turn_id) if run.pending_turn_id else None
    return build_interactive_trial_response(run, turn)


@router.post(
    "/{run_id}/turns/{turn_id}/upload-authorization",
    response_model=UploadAuthorizationResponse,
)
def authorize_participant_upload(
    run_id: UUID,
    turn_id: UUID,
    request: UploadAuthorizationRequest,
    runs: PostgresInteractiveTrialRunRepository = Depends(
        get_interactive_trial_repository
    ),
    storage: ObjectStorageService = Depends(get_object_storage),
) -> UploadAuthorizationResponse:
    content_type = normalize_audio_content_type(request.content_type)
    if content_type not in get_interactive_recording_mime_types():
        raise HTTPException(
            status_code=422, detail="Recording MIME type is not supported."
        )
    try:
        turn = runs.authorize_turn(run_id, turn_id)
    except InteractiveTrialStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    extension = _extension_for(content_type)
    key = f"interactive-trial-runs/{run_id}/turns/{turn.id}/recording.{extension}"
    authorization = storage.create_private_upload(
        key=key,
        content_type=content_type,
        expires_in_seconds=get_interactive_upload_expiry_seconds(),
    )
    return UploadAuthorizationResponse(
        turn_id=turn.id,
        upload_url=authorization.url,
        required_headers=dict(authorization.required_headers),
        expires_in_seconds=authorization.expires_in_seconds,
        max_size_bytes=get_interactive_recording_max_bytes(),
    )


@router.post(
    "/{run_id}/turns/{turn_id}/submit",
    response_model=SubmitParticipantTurnResponse,
    status_code=202,
)
def submit_participant_turn(
    run_id: UUID,
    turn_id: UUID,
    request: SubmitParticipantTurnRequest,
    runs: PostgresInteractiveTrialRunRepository = Depends(
        get_interactive_trial_repository
    ),
    queue: InteractiveTrialQueue = Depends(get_interactive_trial_queue),
    storage: ObjectStorageService = Depends(get_object_storage),
) -> SubmitParticipantTurnResponse:
    turn = runs.get_turn(turn_id)
    if turn is None or turn.run_id != run_id:
        raise HTTPException(status_code=404, detail="Participant turn not found.")
    if turn.scene == "question" and request.is_final is None:
        raise HTTPException(
            status_code=422,
            detail="A witness question must state whether it is final.",
        )
    metadata = None
    key = None
    if request.object:
        # The key is deterministic even before submission; accept the only supported
        # extension that exists and verify it server-side before changing state.
        for mime_type in get_interactive_recording_mime_types():
            candidate = (
                f"interactive-trial-runs/{run_id}/turns/{turn_id}/"
                f"recording.{_extension_for(mime_type)}"
            )
            metadata = storage.get_private_metadata(key=candidate)
            if metadata:
                key = candidate
                break
        if metadata is None or key is None:
            raise HTTPException(
                status_code=422, detail="Objection recording upload was not found."
            )
        if (
            normalize_audio_content_type(metadata.content_type)
            not in get_interactive_recording_mime_types()
            or metadata.size_bytes > get_interactive_recording_max_bytes()
        ):
            raise HTTPException(
                status_code=422,
                detail="Uploaded recording does not satisfy constraints.",
            )
    try:
        stored_turn, enqueue = runs.submit_response(
            run_id,
            turn_id,
            object_requested=request.object,
            is_final=request.is_final,
            bucket=metadata.bucket if metadata else None,
            key=key,
            content_type=metadata.content_type if metadata else None,
            size_bytes=metadata.size_bytes if metadata else None,
            checksum=metadata.checksum if metadata else None,
        )
    except InteractiveTrialStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if enqueue:
        try:
            queue.enqueue_resume(run_id, turn_id)
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="Unable to queue participant response."
            ) from exc
    return SubmitParticipantTurnResponse(
        turn_id=stored_turn.id, status=stored_turn.status
    )


def normalize_audio_content_type(content_type: str) -> str:
    """Return the media type, excluding optional browser codec parameters."""
    return content_type.split(";", 1)[0].strip().lower()


def _extension_for(content_type: str) -> str:
    return {"audio/webm": "webm", "audio/mp4": "m4a", "audio/ogg": "ogg"}.get(
        content_type, "audio"
    )
