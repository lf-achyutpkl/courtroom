from __future__ import annotations

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.ids import FactId, KnowledgeAtomId, WitnessId
from courtroom_engine.domain.visibility import VisibilityScope


class KnowledgeAtom(DomainModel):
    knowledge_atom_id: KnowledgeAtomId
    witness_id: WitnessId
    text: str
    related_fact_ids: tuple[FactId, ...] = ()
    visibility: VisibilityScope | str = VisibilityScope.WITNESS_PRIVATE


class Witness(DomainModel):
    witness_id: WitnessId
    name: str
    called_by: PartySide
    public_summary: str
    knowledge_atom_ids: tuple[KnowledgeAtomId, ...]
