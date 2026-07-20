from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID, uuid4

from ..db.base import CaseFileMessageRecord
from ..db.session import get_session_factory

MessageRole = Literal["human", "ai"]


@dataclass(frozen=True)
class StoredCaseFileMessage:
    id: UUID
    case_file_id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class CaseFileMessageRepository(Protocol):
    def list_for_case_file(self, case_file_id: UUID) -> list[StoredCaseFileMessage]:
        """Return all stored messages for a case file conversation."""
        ...

    def create(
        self,
        *,
        case_file_id: UUID,
        role: MessageRole,
        content: str,
    ) -> StoredCaseFileMessage:
        """Persist a single conversation message."""
        ...


class PostgresCaseFileMessageRepository:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def list_for_case_file(self, case_file_id: UUID) -> list[StoredCaseFileMessage]:
        with self.session_factory() as session:
            records = (
                session.query(CaseFileMessageRecord)
                .filter(CaseFileMessageRecord.case_file_id == case_file_id)
                .order_by(
                    CaseFileMessageRecord.created_at.asc(),
                    CaseFileMessageRecord.id.asc(),
                )
                .all()
            )
            return [_stored_message_from_record(record) for record in records]

    def create(
        self,
        *,
        case_file_id: UUID,
        role: MessageRole,
        content: str,
    ) -> StoredCaseFileMessage:
        record = CaseFileMessageRecord(
            id=uuid4(),
            case_file_id=case_file_id,
            role=role,
            content=content,
        )
        with self.session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _stored_message_from_record(record)


def _stored_message_from_record(record: CaseFileMessageRecord) -> StoredCaseFileMessage:
    return StoredCaseFileMessage(
        id=record.id,
        case_file_id=record.case_file_id,
        role=record.role,
        content=record.content,
        created_at=record.created_at,
    )
