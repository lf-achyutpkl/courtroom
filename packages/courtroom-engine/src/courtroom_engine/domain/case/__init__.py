from __future__ import annotations

from enum import StrEnum
from typing import Literal

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.ids import ActorId, CaseId, PartyId, WitnessId


class CaseKind(StrEnum):
    CIVIL = "civil"
    CRIMINAL = "criminal"


class PartySide(StrEnum):
    PLAINTIFF = "plaintiff"
    PROSECUTION = "prosecution"
    DEFENSE = "defense"


class ActorRole(StrEnum):
    PLAINTIFF_LAWYER = "plaintiff_lawyer"
    PROSECUTION_LAWYER = "prosecution_lawyer"
    DEFENSE_LAWYER = "defense_lawyer"
    WITNESS = "witness"
    TRIAL_JUDGE = "trial_judge"
    JURY = "jury"
    EVALUATOR = "evaluator"
    COACH = "coach"


class CaseMetadata(DomainModel):
    case_id: CaseId
    title: str
    case_kind: CaseKind
    jurisdiction: str = "US-CA"
    trial_type: Literal["jury", "bench"] = "jury"


class Party(DomainModel):
    party_id: PartyId
    name: str
    side: PartySide


class Actor(DomainModel):
    actor_id: ActorId
    role: ActorRole
    name: str
    party_id: PartyId | None = None
    witness_id: WitnessId | None = None
