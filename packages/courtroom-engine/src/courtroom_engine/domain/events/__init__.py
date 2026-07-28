from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from courtroom_engine.domain.base import DomainModel


class CourtroomEvent(DomainModel):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str
    summary: str
