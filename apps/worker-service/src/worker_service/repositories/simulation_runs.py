from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from ..db.session import get_session_factory
from ..orm.records import SimulationRunRecord


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


class PostgresSimulationRunWriter:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def mark_running(self, simulation_run_id: UUID) -> None:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "running"
            record.started_at = record.started_at or _utc_now()
            record.error_message = None
            session.commit()

    def mark_completed(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> None:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "completed"
            record.result = result
            record.error_message = None
            record.completed_at = _utc_now()
            session.commit()

    def mark_failed(self, simulation_run_id: UUID, error_message: str) -> None:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "failed"
            record.error_message = error_message
            record.completed_at = _utc_now()
            session.commit()

    def _get_run(
        self,
        session: Session,
        simulation_run_id: UUID,
    ) -> SimulationRunRecord:
        record = session.get(SimulationRunRecord, simulation_run_id)
        if record is None:
            raise RuntimeError(f"Simulation run not found: {simulation_run_id}")
        return record


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
