from __future__ import annotations

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.ids import ContradictionId, FactId, ObjectiveId
from courtroom_engine.domain.visibility import VisibilityScope


class ExpectedContradiction(DomainModel):
    contradiction_id: ContradictionId
    description: str
    involved_fact_ids: tuple[FactId, ...] = ()
    visibility: VisibilityScope | str = VisibilityScope.EVALUATOR_ONLY


class CoachingReference(DomainModel):
    objective_id: ObjectiveId
    label: str
    ideal_action: str
    visibility: VisibilityScope | str = VisibilityScope.COACH_ONLY


class PrivateSimulationTruth(DomainModel):
    ground_truth_summary: str
    expected_contradictions: tuple[ExpectedContradiction, ...] = ()
    coaching_references: tuple[CoachingReference, ...] = ()
