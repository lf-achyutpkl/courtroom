from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CaseFileRecord(Base):
    __tablename__ = "case_files"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    case_id: Mapped[str] = mapped_column(String, nullable=False)
    case_title: Mapped[str] = mapped_column(String, nullable=False)
    case_type: Mapped[str] = mapped_column(String, nullable=False)
    charge_or_claim: Mapped[str] = mapped_column(String, nullable=False)
    plaintiff_or_prosecution: Mapped[str] = mapped_column(String, nullable=False)
    defendant: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False)
    case_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )


class SimulationRunRecord(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    case_file_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("case_files.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    audio_manifest: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    audio_storage: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CaseFileMessageRecord(Base):
    __tablename__ = "case_file_messages"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    case_file_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("case_files.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )


class InteractiveTrialRunRecord(Base):
    __tablename__ = "interactive_trial_runs"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    case_file_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("case_files.id"), nullable=False
    )
    human_attorney_side: Mapped[str] = mapped_column(String, nullable=False)
    human_witness_plan: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    langgraph_thread_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    state_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    transcript_snapshot: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    result_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    pending_turn_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class ParticipantTurnRecord(Base):
    __tablename__ = "participant_turns"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("interactive_trial_runs.id"),
        nullable=False,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scene: Mapped[str] = mapped_column(String, nullable=False)
    attorney_side: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    object_requested: Mapped[bool | None] = mapped_column(Boolean)
    is_final: Mapped[bool | None] = mapped_column(Boolean)
    object_bucket: Mapped[str | None] = mapped_column(String)
    object_key: Mapped[str | None] = mapped_column(String)
    content_type: Mapped[str | None] = mapped_column(String)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
