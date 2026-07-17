from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Protocol
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ..db.base import SimulationRunRecord
from ..db.session import get_session_factory


SimulationRunStatus = Literal[
    "pending",
    "running",
    "hearing_completed",
    "generating_audio",
    "completed",
    "failed",
]


@dataclass(frozen=True)
class StoredSimulationRun:
    id: UUID
    case_file_id: UUID
    status: SimulationRunStatus
    result: dict[str, object] | None
    audio_manifest: list[dict[str, object]] | None
    audio_storage: dict[str, object] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class SimulationRunRepository(Protocol):
    def get(self, simulation_run_id: UUID) -> StoredSimulationRun | None:
        """Return a stored simulation run by id."""
        ...

    def list_completed_with_audio(self) -> list[StoredSimulationRun]:
        """Return completed simulation runs that have generated audio artifacts."""
        ...

    def create_pending(self, case_file_id: UUID) -> StoredSimulationRun:
        """Create a pending simulation run for a stored case file."""
        ...

    def mark_running(self, simulation_run_id: UUID) -> StoredSimulationRun:
        """Mark a simulation run as running."""
        ...

    def store_result(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> StoredSimulationRun:
        """Store the generated trial result and mark the hearing as completed."""
        ...

    def mark_generating_audio(self, simulation_run_id: UUID) -> StoredSimulationRun:
        """Mark a simulation run as generating audio."""
        ...

    def store_audio_artifacts(
        self,
        simulation_run_id: UUID,
        audio_manifest: list[dict[str, object]],
        audio_storage: dict[str, object],
    ) -> StoredSimulationRun:
        """Store generated audio manifest and storage references."""
        ...

    def mark_completed(
        self,
        simulation_run_id: UUID,
    ) -> StoredSimulationRun:
        """Mark a simulation run as completed."""
        ...

    def mark_failed(
        self,
        simulation_run_id: UUID,
        error_message: str,
    ) -> StoredSimulationRun:
        """Mark a simulation run as failed with a human-readable error."""
        ...


class PostgresSimulationRunRepository:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def get(self, simulation_run_id: UUID) -> StoredSimulationRun | None:
        with self.session_factory() as session:
            record = session.get(SimulationRunRecord, simulation_run_id)
            return (
                _stored_simulation_run_from_record(record)
                if record is not None
                else None
            )

    def create_pending(self, case_file_id: UUID) -> StoredSimulationRun:
        record = SimulationRunRecord(
            id=uuid4(),
            case_file_id=case_file_id,
            status="pending",
        )
        with self.session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

    def list_completed_with_audio(self) -> list[StoredSimulationRun]:
        with self.session_factory() as session:
            records = (
                session.query(SimulationRunRecord)
                .filter(SimulationRunRecord.status == "completed")
                .filter(SimulationRunRecord.audio_manifest.is_not(None))
                .order_by(
                    SimulationRunRecord.completed_at.desc(),
                    SimulationRunRecord.created_at.desc(),
                )
                .all()
            )
            return [_stored_simulation_run_from_record(record) for record in records]

    def store_result(
        self,
        simulation_run_id: UUID,
        result: dict[str, object],
    ) -> StoredSimulationRun:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "hearing_completed"
            record.result = result
            record.error_message = None
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

    def mark_generating_audio(self, simulation_run_id: UUID) -> StoredSimulationRun:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "generating_audio"
            record.error_message = None
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

    def store_audio_artifacts(
        self,
        simulation_run_id: UUID,
        audio_manifest: list[dict[str, object]],
        audio_storage: dict[str, object],
    ) -> StoredSimulationRun:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.audio_manifest = audio_manifest
            record.audio_storage = audio_storage
            record.error_message = None
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

    def mark_running(self, simulation_run_id: UUID) -> StoredSimulationRun:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "running"
            record.started_at = record.started_at or _utc_now()
            record.error_message = None
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

    def mark_completed(
        self,
        simulation_run_id: UUID,
    ) -> StoredSimulationRun:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "completed"
            record.error_message = None
            record.completed_at = _utc_now()
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

    def mark_failed(
        self,
        simulation_run_id: UUID,
        error_message: str,
    ) -> StoredSimulationRun:
        with self.session_factory() as session:
            record = self._get_run(session, simulation_run_id)
            record.status = "failed"
            record.error_message = error_message
            record.completed_at = _utc_now()
            session.commit()
            session.refresh(record)
            return _stored_simulation_run_from_record(record)

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


def _stored_simulation_run_from_record(
    record: SimulationRunRecord,
) -> StoredSimulationRun:
    return StoredSimulationRun(
        id=record.id,
        case_file_id=record.case_file_id,
        status=record.status,  # type: ignore[arg-type]
        result=record.result,
        audio_manifest=record.audio_manifest,  # type: ignore[arg-type]
        audio_storage=record.audio_storage,  # type: ignore[arg-type]
        error_message=record.error_message,
        created_at=record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
    )
