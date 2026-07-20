from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from courtroom_domain import EditAction, manual_operation_from_payload
from ...api.deps import get_case_file_repository
from ...core.config import get_database_url
from ...repositories.case_files import (
    CaseFileNotFoundError,
    CaseFileRepository,
    CaseFileRevisionConflictError,
    StoredCaseFile,
)
from ...schemas.case_files import (
    CaseFileMessageRequest,
    CaseFileResponse,
    ManualMutationRequest,
    ManualMutationResponse,
)
from ...services.case_file_factory import build_initial_case_file
from ...workflows.case_editor import stream_case_editor_response


router = APIRouter()


def _response_from_record(record: StoredCaseFile) -> CaseFileResponse:
    return CaseFileResponse(
        id=record.id,
        status=record.status,
        revision=record.revision,
        case_file=record.case_file,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/case-files",
    response_model=CaseFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case_file(
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
) -> CaseFileResponse:
    case_file = build_initial_case_file()
    record = case_file_repository.create(case_file)
    return _response_from_record(record)


@router.get("/case-files/{case_file_id}", response_model=CaseFileResponse)
def get_case_file(
    case_file_id: UUID,
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
) -> CaseFileResponse:
    record = case_file_repository.get(case_file_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found.",
        )
    return _response_from_record(record)


@router.post(
    "/case-files/{case_file_id}/mutations",
    response_model=ManualMutationResponse,
)
def mutate_case_file(
    case_file_id: UUID,
    request: ManualMutationRequest,
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
) -> ManualMutationResponse:
    stored = case_file_repository.get(case_file_id)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found.",
        )

    try:
        operation = manual_operation_from_payload(
            case_file=stored.case_file,
            action=EditAction(request.action),
            card_type=request.card_type,
            card_id=request.card_id,
            content=request.content,
        )
        updated = case_file_repository.apply_operation(
            case_file_id,
            operation,
            expected_revision=request.expected_revision,
        )
    except CaseFileRevisionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except CaseFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found.",
        ) from None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ManualMutationResponse(operation=operation, revision=updated.revision)


@router.post("/case-files/{case_file_id}/messages")
def post_case_file_message(
    case_file_id: UUID,
    request: CaseFileMessageRequest,
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
) -> StreamingResponse:
    if case_file_repository.get(case_file_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found.",
        )

    return StreamingResponse(
        stream_case_editor_response(
            case_file_id=case_file_id,
            message=request.message,
            selected_card=request.selected_card,
            case_files=case_file_repository,
            database_url=get_database_url(),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "x-vercel-ai-ui-message-stream": "v1",
        },
    )
