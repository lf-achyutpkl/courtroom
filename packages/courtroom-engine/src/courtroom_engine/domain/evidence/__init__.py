from __future__ import annotations

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.ids import ElementId, EvidenceId, FactId
from courtroom_engine.domain.visibility import VisibilityScope


class Fact(DomainModel):
    fact_id: FactId
    text: str
    visibility: VisibilityScope | str = VisibilityScope.PUBLIC_CASE
    supports_element_ids: tuple[ElementId, ...] = ()
    disputed: bool = True


class EvidenceItem(DomainModel):
    evidence_id: EvidenceId
    title: str
    description: str
    offered_by: PartySide
    visibility: VisibilityScope | str = VisibilityScope.PUBLIC_CASE
    supports_fact_ids: tuple[FactId, ...] = ()
    foundation_required: bool = True
