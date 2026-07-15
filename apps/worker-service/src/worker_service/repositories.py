from __future__ import annotations

from typing import Protocol
from uuid import UUID

import psycopg
from courtroom_domain import CaseFile
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class CaseFileReader(Protocol):
    def get(self, case_file_id: UUID) -> CaseFile | None:
        """Return a stored case file by storage id."""


class SimulationRunWriter(Protocol):
    def mark_running(self, simulation_run_id: UUID) -> None:
        """Mark a simulation run as running."""

    def mark_completed(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> None:
        """Persist a completed simulation result."""

    def mark_failed(self, simulation_run_id: UUID, error_message: str) -> None:
        """Persist a failed simulation result."""


class PostgresCaseFileReader:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def get(self, case_file_id: UUID) -> CaseFile | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT case_file
                    FROM case_files
                    WHERE id = %(id)s
                    """,
                    {"id": case_file_id},
                )
                row = cursor.fetchone()
        return CaseFile.model_validate(row["case_file"]) if row is not None else None


class PostgresSimulationRunWriter:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def mark_running(self, simulation_run_id: UUID) -> None:
        self._execute(
            """
            UPDATE simulation_runs
            SET status = 'running',
                started_at = COALESCE(started_at, NOW()),
                error_message = NULL
            WHERE id = %(id)s
            """,
            {"id": simulation_run_id},
        )

    def mark_completed(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> None:
        self._execute(
            """
            UPDATE simulation_runs
            SET status = 'completed',
                result = %(result)s,
                error_message = NULL,
                completed_at = NOW()
            WHERE id = %(id)s
            """,
            {"id": simulation_run_id, "result": Jsonb(result)},
        )

    def mark_failed(self, simulation_run_id: UUID, error_message: str) -> None:
        self._execute(
            """
            UPDATE simulation_runs
            SET status = 'failed',
                error_message = %(error_message)s,
                completed_at = NOW()
            WHERE id = %(id)s
            """,
            {"id": simulation_run_id, "error_message": error_message},
        )

    def _execute(self, query: str, parameters: dict[str, object]) -> None:
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
