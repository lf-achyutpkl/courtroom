"""Persistence and state transitions for public AI-vs-human trial runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Protocol
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ..db.base import InteractiveTrialRunRecord, ParticipantTurnRecord
from ..db.session import get_session_factory

InteractiveTrialRunStatus = Literal[
    "queued", "running", "awaiting_human", "completed", "failed"
]
ParticipantTurnStatus = Literal["pending_upload", "submitted", "resuming", "consumed"]


class InteractiveTrialStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredParticipantTurn:
    id: UUID
    run_id: UUID
    turn_number: int
    scene: str
    attorney_side: str
    status: ParticipantTurnStatus
    object_requested: bool | None
    is_final: bool | None
    object_bucket: str | None
    object_key: str | None
    content_type: str | None
    size_bytes: int | None
    checksum: str | None
    submitted_at: datetime | None
    resumed_at: datetime | None


@dataclass(frozen=True)
class StoredInteractiveTrialRun:
    id: UUID
    case_file_id: UUID
    human_attorney_side: Literal["prosecution", "defense"]
    human_witness_plan: list[str]
    langgraph_thread_id: str
    status: InteractiveTrialRunStatus
    state_snapshot: dict[str, object] | None
    transcript_snapshot: list[dict[str, object]] | None
    result_snapshot: dict[str, object] | None
    pending_turn_id: UUID | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class InteractiveTrialRunRepository(Protocol):
    def create(
        self,
        case_file_id: UUID,
        human_attorney_side: str,
        human_witness_plan: list[str],
    ) -> StoredInteractiveTrialRun: ...
    def get(self, run_id: UUID) -> StoredInteractiveTrialRun | None: ...
    def get_turn(self, turn_id: UUID) -> StoredParticipantTurn | None: ...


class PostgresInteractiveTrialRunRepository:
    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def create(
        self,
        case_file_id: UUID,
        human_attorney_side: str,
        human_witness_plan: list[str],
    ) -> StoredInteractiveTrialRun:
        if human_attorney_side not in {"prosecution", "defense"}:
            raise ValueError("human_attorney_side must be prosecution or defense")
        if not human_witness_plan or len(human_witness_plan) != len(
            set(human_witness_plan)
        ):
            raise ValueError("human_witness_plan must contain unique witness IDs")
        record = InteractiveTrialRunRecord(
            id=uuid4(),
            case_file_id=case_file_id,
            human_attorney_side=human_attorney_side,
            human_witness_plan=human_witness_plan,
            langgraph_thread_id=str(uuid4()),
            status="queued",
        )
        with self.session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return _stored_run(record)

    def get(self, run_id: UUID) -> StoredInteractiveTrialRun | None:
        with self.session_factory() as session:
            record = session.get(InteractiveTrialRunRecord, run_id)
            return _stored_run(record) if record else None

    def get_turn(self, turn_id: UUID) -> StoredParticipantTurn | None:
        with self.session_factory() as session:
            record = session.get(ParticipantTurnRecord, turn_id)
            return _stored_turn(record) if record else None

    def mark_running(
        self, run_id: UUID, *, turn_id: UUID | None = None
    ) -> StoredInteractiveTrialRun:
        with self.session_factory() as session:
            run = self._locked_run(session, run_id)
            if run.status in {"completed", "failed"}:
                raise InteractiveTrialStateError("Interactive trial is terminal")
            if turn_id is not None and run.pending_turn_id != turn_id:
                raise InteractiveTrialStateError("Participant turn is stale")
            if turn_id is not None:
                turn = self._locked_turn(session, turn_id)
                if turn.status in {"resuming", "consumed"}:
                    return _stored_run(run)
                if turn.status != "submitted":
                    raise InteractiveTrialStateError(
                        "Participant recording has not been submitted"
                    )
                turn.status = "resuming"
                turn.resumed_at = _now()
            run.status = "running"
            run.started_at = run.started_at or _now()
            run.error_message = None
            run.updated_at = _now()
            session.commit()
            session.refresh(run)
            return _stored_run(run)

    def store_progress(
        self,
        run_id: UUID,
        *,
        state_snapshot: dict[str, object],
        interrupt: dict[str, object] | None,
        consumed_turn_id: UUID | None = None,
    ) -> StoredInteractiveTrialRun:
        with self.session_factory() as session:
            run = self._locked_run(session, run_id)
            if run.status in {"completed", "failed"}:
                return _stored_run(run)
            if consumed_turn_id is not None:
                turn = self._locked_turn(session, consumed_turn_id)
                if turn.status == "consumed":
                    return _stored_run(run)
                turn.status = "consumed"
            run.state_snapshot = state_snapshot
            transcript = state_snapshot.get("full_trial_transcript")
            run.transcript_snapshot = transcript if isinstance(transcript, list) else []
            if interrupt is None:
                run.status = "completed"
                run.pending_turn_id = None
                run.result_snapshot = state_snapshot
                run.completed_at = _now()
            else:
                next_turn = self._create_pending_turn(session, run, interrupt)
                run.status = "awaiting_human"
                run.pending_turn_id = next_turn.id
            run.updated_at = _now()
            session.commit()
            session.refresh(run)
            return _stored_run(run)

    def authorize_turn(self, run_id: UUID, turn_id: UUID) -> StoredParticipantTurn:
        with self.session_factory() as session:
            run = self._locked_run(session, run_id)
            if run.status != "awaiting_human" or run.pending_turn_id != turn_id:
                raise InteractiveTrialStateError("Participant turn is not active")
            turn = self._locked_turn(session, turn_id)
            if turn.status not in {"pending_upload", "submitted"}:
                raise InteractiveTrialStateError(
                    "Participant turn cannot accept an upload"
                )
            return _stored_turn(turn)

    def submit_response(
        self,
        run_id: UUID,
        turn_id: UUID,
        *,
        object_requested: bool,
        is_final: bool | None = None,
        bucket: str | None = None,
        key: str | None = None,
        content_type: str | None = None,
        size_bytes: int | None = None,
        checksum: str | None,
    ) -> tuple[StoredParticipantTurn, bool]:
        with self.session_factory() as session:
            run = self._locked_run(session, run_id)
            if run.status != "awaiting_human" or run.pending_turn_id != turn_id:
                raise InteractiveTrialStateError("Participant turn is stale")
            turn = self._locked_turn(session, turn_id)
            if turn.status in {"submitted", "resuming", "consumed"}:
                return _stored_turn(turn), False
            if turn.status != "pending_upload":
                raise InteractiveTrialStateError("Participant turn cannot be submitted")
            if object_requested and not all(
                (bucket, key, content_type, size_bytes is not None)
            ):
                raise InteractiveTrialStateError("An objection requires a recording")
            turn.object_requested = object_requested
            turn.is_final = is_final
            turn.object_bucket, turn.object_key = bucket, key
            turn.content_type, turn.size_bytes, turn.checksum = (
                content_type,
                size_bytes,
                checksum,
            )
            turn.status, turn.submitted_at, turn.updated_at = (
                "submitted",
                _now(),
                _now(),
            )
            session.commit()
            session.refresh(turn)
            return _stored_turn(turn), True

    def mark_failed(self, run_id: UUID, message: str) -> StoredInteractiveTrialRun:
        with self.session_factory() as session:
            run = self._locked_run(session, run_id)
            if run.status == "completed":
                return _stored_run(run)
            run.status, run.error_message, run.completed_at, run.updated_at = (
                "failed",
                message,
                _now(),
                _now(),
            )
            session.commit()
            session.refresh(run)
            return _stored_run(run)

    def _create_pending_turn(
        self,
        session: Session,
        run: InteractiveTrialRunRecord,
        interrupt: dict[str, object],
    ) -> ParticipantTurnRecord:
        if run.pending_turn_id:
            previous = session.get(ParticipantTurnRecord, run.pending_turn_id)
            if previous and previous.status == "pending_upload":
                return previous
        scene = str(interrupt.get("kind", "human_turn")).removeprefix("human_")
        side = str(interrupt.get("attorney_side", run.human_attorney_side))
        previous_count = (
            session.query(ParticipantTurnRecord).filter_by(run_id=run.id).count()
        )
        turn = ParticipantTurnRecord(
            id=uuid4(),
            run_id=run.id,
            turn_number=previous_count + 1,
            scene=scene,
            attorney_side=side,
            status="pending_upload",
        )
        session.add(turn)
        session.flush()
        return turn

    @staticmethod
    def _locked_run(session: Session, run_id: UUID) -> InteractiveTrialRunRecord:
        record = (
            session.query(InteractiveTrialRunRecord)
            .with_for_update()
            .filter_by(id=run_id)
            .one_or_none()
        )
        if record is None:
            raise InteractiveTrialStateError("Interactive trial was not found")
        return record

    @staticmethod
    def _locked_turn(session: Session, turn_id: UUID) -> ParticipantTurnRecord:
        record = (
            session.query(ParticipantTurnRecord)
            .with_for_update()
            .filter_by(id=turn_id)
            .one_or_none()
        )
        if record is None:
            raise InteractiveTrialStateError("Participant turn was not found")
        return record


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stored_run(record: InteractiveTrialRunRecord) -> StoredInteractiveTrialRun:
    return StoredInteractiveTrialRun(
        id=record.id,
        case_file_id=record.case_file_id,
        human_attorney_side=record.human_attorney_side,  # type: ignore[arg-type]
        human_witness_plan=list(record.human_witness_plan or []),
        langgraph_thread_id=record.langgraph_thread_id,
        status=record.status,  # type: ignore[arg-type]
        state_snapshot=record.state_snapshot,
        transcript_snapshot=record.transcript_snapshot,
        result_snapshot=record.result_snapshot,
        pending_turn_id=record.pending_turn_id,
        error_message=record.error_message,
        created_at=record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
    )


def _stored_turn(record: ParticipantTurnRecord) -> StoredParticipantTurn:
    return StoredParticipantTurn(
        id=record.id,
        run_id=record.run_id,
        turn_number=record.turn_number,
        scene=record.scene,
        attorney_side=record.attorney_side,
        status=record.status,  # type: ignore[arg-type]
        object_requested=record.object_requested,
        is_final=record.is_final,
        object_bucket=record.object_bucket,
        object_key=record.object_key,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        checksum=record.checksum,
        submitted_at=record.submitted_at,
        resumed_at=record.resumed_at,
    )
