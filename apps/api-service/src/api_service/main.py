from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from courtroom_domain import CaseFile

from .config import get_database_url
from .dummy_case_file import build_dummy_case_file
from .repository import CaseFileRepository, PostgresCaseFileRepository, StoredCaseFile


class CaseFileResponse(BaseModel):
    id: UUID
    case_file: CaseFile
    created_at: datetime


def _response_from_record(record: StoredCaseFile) -> CaseFileResponse:
    return CaseFileResponse(
        id=record.id,
        case_file=record.case_file,
        created_at=record.created_at,
    )


def get_case_file_repository() -> CaseFileRepository:
    return PostgresCaseFileRepository(get_database_url())


def create_app(repository: CaseFileRepository | None = None) -> FastAPI:
    app = FastAPI(title="Courtroom API Service")

    def repository_dependency() -> CaseFileRepository:
        return repository if repository is not None else get_case_file_repository()

    @app.post(
        "/case-files",
        response_model=CaseFileResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_case_file(
        case_file_repository: CaseFileRepository = Depends(repository_dependency),
    ) -> CaseFileResponse:
        case_file = build_dummy_case_file()
        record = case_file_repository.create(case_file)
        return _response_from_record(record)

    @app.get("/case-files/{case_file_id}", response_model=CaseFileResponse)
    def get_case_file(
        case_file_id: UUID,
        case_file_repository: CaseFileRepository = Depends(repository_dependency),
    ) -> CaseFileResponse:
        record = case_file_repository.get(case_file_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case file not found.",
            )
        return _response_from_record(record)

    return app


app = create_app()
