from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from courtroom_domain import CaseEditOperation, CaseFile, apply_case_edit_result

from ..db.base import CaseFileRecord
from ..db.session import get_session_factory


@dataclass(frozen=True)
class StoredCaseFile:
    id: UUID
    case_file: CaseFile
    status: str
    revision: int
    created_at: datetime
    updated_at: datetime


class CaseFileNotFoundError(Exception):
    pass


class CaseFileRevisionConflictError(Exception):
    pass


class CaseFileRepository(Protocol):
    def create(self, case_file: CaseFile, *, status: str = "draft") -> StoredCaseFile:
        """Persist a case file and return the stored record."""
        ...

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        """Return a stored case file by storage id."""
        ...

    def apply_operation(
        self,
        case_file_id: UUID,
        operation: CaseEditOperation,
        *,
        expected_revision: int,
    ) -> StoredCaseFile:
        """Apply a scoped edit with optimistic concurrency."""
        ...

    def replace_case_file(
        self,
        case_file_id: UUID,
        case_file: CaseFile,
        *,
        expected_revision: int,
        status: str | None = None,
    ) -> StoredCaseFile:
        """Replace the stored case file with optimistic concurrency."""
        ...


class PostgresCaseFileRepository:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def create(self, case_file: CaseFile, *, status: str = "draft") -> StoredCaseFile:
        payload = case_file.model_dump(mode="json")
        timestamp = datetime.now(timezone.utc)
        record = CaseFileRecord(
            id=uuid4(),
            case_id=case_file.case_id,
            case_title=case_file.case_title,
            case_type=case_file.case_type,
            charge_or_claim=case_file.charge_or_claim,
            plaintiff_or_prosecution=case_file.parties.plaintiff_or_prosecution,
            defendant=case_file.parties.defendant,
            status=status,
            revision=1,
            case_json=payload,
            created_at=timestamp,
            updated_at=timestamp,
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

    def apply_operation(
        self,
        case_file_id: UUID,
        operation: CaseEditOperation,
        *,
        expected_revision: int,
    ) -> StoredCaseFile:
        with self.session_factory() as session:
            record = session.get(CaseFileRecord, case_file_id)
            if record is None:
                raise CaseFileNotFoundError(f"Case file {case_file_id} was not found")
            _assert_expected_revision(record.revision, expected_revision)
            current_case_file = CaseFile.model_validate(record.case_json)
            next_case_file = apply_case_edit_result(current_case_file, operation)
            _update_record(record, next_case_file, status=record.status)
            session.add(record)
            session.commit()
            session.refresh(record)
            return _stored_case_file_from_record(record)

    def replace_case_file(
        self,
        case_file_id: UUID,
        case_file: CaseFile,
        *,
        expected_revision: int,
        status: str | None = None,
    ) -> StoredCaseFile:
        with self.session_factory() as session:
            record = session.get(CaseFileRecord, case_file_id)
            if record is None:
                raise CaseFileNotFoundError(f"Case file {case_file_id} was not found")
            _assert_expected_revision(record.revision, expected_revision)
            _update_record(record, case_file, status=status or record.status)
            session.add(record)
            session.commit()
            session.refresh(record)
            return _stored_case_file_from_record(record)


def _assert_expected_revision(actual_revision: int, expected_revision: int) -> None:
    if actual_revision != expected_revision:
        raise CaseFileRevisionConflictError(
            f"Expected revision {expected_revision}, found {actual_revision}"
        )


def _update_record(record: CaseFileRecord, case_file: CaseFile, *, status: str) -> None:
    record.case_id = case_file.case_id
    record.case_title = case_file.case_title
    record.case_type = case_file.case_type
    record.charge_or_claim = case_file.charge_or_claim
    record.plaintiff_or_prosecution = case_file.parties.plaintiff_or_prosecution
    record.defendant = case_file.parties.defendant
    record.status = status
    record.case_json = case_file.model_dump(mode="json")
    record.revision += 1
    record.updated_at = datetime.now(timezone.utc)


def _stored_case_file_from_record(record: CaseFileRecord) -> StoredCaseFile:
    return StoredCaseFile(
        id=record.id,
        case_file=CaseFile.model_validate(record.case_json),
        status=record.status,
        revision=record.revision,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
