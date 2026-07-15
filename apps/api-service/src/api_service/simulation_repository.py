from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


SimulationRunStatus = Literal["pending", "running", "completed", "failed"]


@dataclass(frozen=True)
class StoredSimulationRun:
    id: UUID
    case_file_id: UUID
    status: SimulationRunStatus
    result: dict[str, object] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class SimulationRunRepository(Protocol):
    def create_pending(self, case_file_id: UUID) -> StoredSimulationRun:
        """Create a pending simulation run for a stored case file."""

    def mark_running(self, simulation_run_id: UUID) -> StoredSimulationRun:
        """Mark a simulation run as running."""

    def mark_completed(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> StoredSimulationRun:
        """Mark a simulation run as completed with the final result."""

    def mark_failed(
        self,
        simulation_run_id: UUID,
        error_message: str,
    ) -> StoredSimulationRun:
        """Mark a simulation run as failed with a human-readable error."""


class PostgresSimulationRunRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def create_pending(self, case_file_id: UUID) -> StoredSimulationRun:
        run_id = uuid4()
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO simulation_runs (id, case_file_id, status)
                    VALUES (%(id)s, %(case_file_id)s, 'pending')
                    RETURNING *
                    """,
                    {"id": run_id, "case_file_id": case_file_id},
                )
                row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Postgres did not return the inserted simulation run.")
        return _stored_simulation_run_from_row(row)

    def mark_running(self, simulation_run_id: UUID) -> StoredSimulationRun:
        return self._update_status(
            simulation_run_id,
            """
            UPDATE simulation_runs
            SET status = 'running',
                started_at = COALESCE(started_at, NOW()),
                error_message = NULL
            WHERE id = %(id)s
            RETURNING *
            """,
            {"id": simulation_run_id},
        )

    def mark_completed(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> StoredSimulationRun:
        return self._update_status(
            simulation_run_id,
            """
            UPDATE simulation_runs
            SET status = 'completed',
                result = %(result)s,
                error_message = NULL,
                completed_at = NOW()
            WHERE id = %(id)s
            RETURNING *
            """,
            {"id": simulation_run_id, "result": Jsonb(result)},
        )

    def mark_failed(
        self,
        simulation_run_id: UUID,
        error_message: str,
    ) -> StoredSimulationRun:
        return self._update_status(
            simulation_run_id,
            """
            UPDATE simulation_runs
            SET status = 'failed',
                error_message = %(error_message)s,
                completed_at = NOW()
            WHERE id = %(id)s
            RETURNING *
            """,
            {"id": simulation_run_id, "error_message": error_message},
        )

    def _update_status(
        self,
        simulation_run_id: UUID,
        query: str,
        parameters: dict[str, object],
    ) -> StoredSimulationRun:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                row = cursor.fetchone()
        if row is None:
            raise RuntimeError(f"Simulation run not found: {simulation_run_id}")
        return _stored_simulation_run_from_row(row)


def _stored_simulation_run_from_row(row: dict[str, object]) -> StoredSimulationRun:
    return StoredSimulationRun(
        id=UUID(str(row["id"])),
        case_file_id=UUID(str(row["case_file_id"])),
        status=row["status"],  # type: ignore[arg-type]
        result=row["result"],  # type: ignore[arg-type]
        error_message=row["error_message"],  # type: ignore[arg-type]
        created_at=row["created_at"],  # type: ignore[arg-type]
        started_at=row["started_at"],  # type: ignore[arg-type]
        completed_at=row["completed_at"],  # type: ignore[arg-type]
    )
