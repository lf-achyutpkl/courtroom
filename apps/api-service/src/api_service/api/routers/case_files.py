from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...api.deps import get_case_file_repository
from ...repositories.case_files import CaseFileRepository, StoredCaseFile
from ...schemas.case_files import CaseFileResponse
from ...services.case_file_factory import build_dummy_case_file


router = APIRouter()


def _response_from_record(record: StoredCaseFile) -> CaseFileResponse:
    return CaseFileResponse(
        id=record.id,
        case_file=record.case_file,
        created_at=record.created_at,
    )


@router.post(
    "/case-files",
    response_model=CaseFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case_file(
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
) -> CaseFileResponse:
    case_file = build_dummy_case_file()
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
