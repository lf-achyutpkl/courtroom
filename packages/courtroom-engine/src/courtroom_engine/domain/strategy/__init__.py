from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.ids import (
    ElementId,
    EvidenceId,
    FactId,
    ObjectiveId,
    WitnessId,
)


class ObjectiveStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    SATISFIED = "satisfied"
    FAILED = "failed"


class StrategyValidationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


class StrategyNote(DomainModel):
    objective_id: ObjectiveId
    label: str
    description: str


class CaseTheory(DomainModel):
    theory_id: str
    side: PartySide
    theme: str
    core_claim: str
    target_element_ids: tuple[ElementId, ...] = ()
    supporting_fact_ids: tuple[FactId, ...] = ()
    dangerous_fact_ids: tuple[FactId, ...] = ()


class StrategicObjective(DomainModel):
    objective_id: ObjectiveId
    description: str
    target_element_ids: tuple[ElementId, ...] = ()
    target_fact_ids: tuple[FactId, ...] = ()
    priority: float = Field(ge=0, le=1)
    success_signals: tuple[str, ...]
    failure_signals: tuple[str, ...] = ()
    status: ObjectiveStatus = ObjectiveStatus.PLANNED


class WitnessPlan(DomainModel):
    witness_id: WitnessId
    calling_side: PartySide
    objective_ids: tuple[ObjectiveId, ...] = ()
    direct_topics: tuple[str, ...] = ()
    cross_risks: tuple[str, ...] = ()
    order: int = Field(ge=1)
    omit: bool = False


class EvidencePlan(DomainModel):
    evidence_id: EvidenceId
    offering_side: PartySide
    objective_ids: tuple[ObjectiveId, ...] = ()
    fact_ids: tuple[FactId, ...] = ()
    through_witness_id: WitnessId | None = None
    foundation_required: bool = True
    expected_objections: tuple[str, ...] = ()
    fallback: str = ""


class OpponentRiskRecord(DomainModel):
    risk_id: str
    side: PartySide
    description: str
    related_fact_ids: tuple[FactId, ...] = ()
    related_evidence_ids: tuple[EvidenceId, ...] = ()
    severity: float = Field(ge=0, le=1)


class ObjectiveRuntimeState(DomainModel):
    objective_id: ObjectiveId
    status: ObjectiveStatus = ObjectiveStatus.PLANNED
    progress_score: float = Field(default=0, ge=0, le=1)
    supporting_event_ids: tuple[str, ...] = ()


class StrategyValidationRecord(DomainModel):
    status: StrategyValidationStatus
    invalid_references: tuple[str, ...] = ()
    messages: tuple[str, ...] = ()


class PartyStrategy(DomainModel):
    strategy_id: str
    side: PartySide
    theory: CaseTheory
    objectives: tuple[StrategicObjective, ...]
    witness_plans: tuple[WitnessPlan, ...] = ()
    evidence_plans: tuple[EvidencePlan, ...] = ()
    opponent_risks: tuple[OpponentRiskRecord, ...] = ()
    objective_states: tuple[ObjectiveRuntimeState, ...] = ()
    validation: StrategyValidationRecord = Field(
        default_factory=lambda: StrategyValidationRecord(
            status=StrategyValidationStatus.VALID
        )
    )
