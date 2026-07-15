from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from courtroom_domain import CaseFile
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


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
        self.database_url = database_url

    def create(self, case_file: CaseFile) -> StoredCaseFile:
        record_id = uuid4()
        payload = case_file.model_dump(mode="json")
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_files (
                        id,
                        case_id,
                        case_type,
                        charge_or_claim,
                        plaintiff_or_prosecution,
                        defendant,
                        case_file
                    )
                    VALUES (
                        %(id)s,
                        %(case_id)s,
                        %(case_type)s,
                        %(charge_or_claim)s,
                        %(plaintiff_or_prosecution)s,
                        %(defendant)s,
                        %(case_file)s
                    )
                    RETURNING id, case_file, created_at
                    """,
                    {
                        "id": record_id,
                        "case_id": case_file.case_id,
                        "case_type": case_file.case_type,
                        "charge_or_claim": case_file.charge_or_claim,
                        "plaintiff_or_prosecution": (
                            case_file.parties.plaintiff_or_prosecution
                        ),
                        "defendant": case_file.parties.defendant,
                        "case_file": Jsonb(payload),
                    },
                )
                row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Postgres did not return the inserted case file.")
        return _stored_case_file_from_row(row)

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, case_file, created_at
                    FROM case_files
                    WHERE id = %(id)s
                    """,
                    {"id": case_file_id},
                )
                row = cursor.fetchone()
        return _stored_case_file_from_row(row) if row is not None else None


def _stored_case_file_from_row(row: dict[str, object]) -> StoredCaseFile:
    return StoredCaseFile(
        id=UUID(str(row["id"])),
        case_file=CaseFile.model_validate(row["case_file"]),
        created_at=row["created_at"],  # type: ignore[arg-type]
    )
