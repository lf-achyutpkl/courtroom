from __future__ import annotations

from typing import Protocol
from uuid import UUID

from courtroom_domain import CaseFile

from ..db.session import get_session_factory
from ..orm.records import CaseFileRecord


class CaseFileReader(Protocol):
    def get(self, case_file_id: UUID) -> CaseFile | None:
        """Return a stored case file by storage id."""


class PostgresCaseFileReader:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def get(self, case_file_id: UUID) -> CaseFile | None:
        with self.session_factory() as session:
            record = session.get(CaseFileRecord, case_file_id)
            return (
                CaseFile.model_validate(record.case_file)
                if record is not None
                else None
            )
