from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from courtroom_domain import CaseFile

from ..db.base import CaseFileRecord
from ..db.session import get_session_factory


@dataclass(frozen=True)
class StoredCaseFile:
    id: UUID
    case_file: CaseFile
    created_at: datetime


class CaseFileRepository(Protocol):
    def create(self, case_file: CaseFile) -> StoredCaseFile:
        """Persist a case file and return the stored record."""

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        """Return a stored case file by storage id."""


class PostgresCaseFileRepository:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def create(self, case_file: CaseFile) -> StoredCaseFile:
        payload = case_file.model_dump(mode="json")
        record = CaseFileRecord(
            id=uuid4(),
            case_id=case_file.case_id,
            case_type=case_file.case_type,
            charge_or_claim=case_file.charge_or_claim,
            plaintiff_or_prosecution=case_file.parties.plaintiff_or_prosecution,
            defendant=case_file.parties.defendant,
            case_file=payload,
        )
        with self.session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _stored_case_file_from_record(record)

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        with self.session_factory() as session:
            record = session.get(CaseFileRecord, case_file_id)
            return _stored_case_file_from_record(record) if record is not None else None


def _stored_case_file_from_record(record: CaseFileRecord) -> StoredCaseFile:
    return StoredCaseFile(
        id=record.id,
        case_file=CaseFile.model_validate(record.case_file),
        created_at=record.created_at,
    )
