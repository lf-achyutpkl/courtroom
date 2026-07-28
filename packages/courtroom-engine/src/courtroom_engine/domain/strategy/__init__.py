from __future__ import annotations

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.ids import ObjectiveId


class StrategyNote(DomainModel):
    objective_id: ObjectiveId
    label: str
    description: str
