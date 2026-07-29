from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.ids import ActorId
from courtroom_engine.domain.procedure import TrialPhase


class CourtroomEventType(StrEnum):
    SESSION_INITIALIZED = "session_initialized"
    CASE_ANALYZED = "case_analyzed"
    STRATEGY_PLANNED = "strategy_planned"
    OPENING_DELIVERED = "opening_delivered"
    WITNESS_SELECTED = "witness_selected"
    QUESTION_ASKED = "question_asked"
    OBJECTION_DECIDED = "objection_decided"
    RULING_ENTERED = "ruling_entered"
    WITNESS_ANSWERED = "witness_answered"
    EVIDENCE_UPDATED = "evidence_updated"
    CONTRADICTION_DETECTED = "contradiction_detected"
    OBJECTIVE_ASSESSED = "objective_assessed"
    CLOSING_DELIVERED = "closing_delivered"
    DELIBERATION_COMPLETED = "deliberation_completed"
    EVALUATION_COMPLETED = "evaluation_completed"
    COACHING_COMPLETED = "coaching_completed"


class CourtroomEvent(DomainModel):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: CourtroomEventType | str
    summary: str
    phase: TrialPhase | str | None = None
    actor_id: ActorId | None = None
    visibility: str = "public"
    cited_object_ids: tuple[str, ...] = ()
    payload_summary: str = ""
