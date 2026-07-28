from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.ids import ActorId, EvidenceId, WitnessId


class TrialPhase(StrEnum):
    INITIALIZATION = "initialization"
    CASE_INTELLIGENCE = "case_intelligence"
    STRATEGY = "strategy"
    OPENING = "opening"
    WITNESS_EXAMINATION = "witness_examination"
    CLOSING_RECORD = "closing_record"
    CLOSING = "closing"
    DELIBERATION = "deliberation"
    EVALUATION = "evaluation"
    COMPLETE = "complete"


class ExaminationMode(StrEnum):
    DIRECT = "direct"
    CROSS = "cross"
    REDIRECT = "redirect"
    RECROSS = "recross"


class ActionType(StrEnum):
    PLAN_STRATEGY = "plan_strategy"
    SELECT_WITNESS = "select_witness"
    PLAN_EXAMINATION_OBJECTIVE = "plan_examination_objective"
    PLAN_TACTICAL_ACTION = "plan_tactical_action"
    ASK_QUESTION = "ask_question"
    OBJECT = "object"
    RULE_ON_OBJECTION = "rule_on_objection"
    ANSWER_PENDING_QUESTION = "answer_pending_question"
    OFFER_EVIDENCE = "offer_evidence"
    ADMIT_EVIDENCE = "admit_evidence"
    ARGUE = "argue"
    INSTRUCT_JURY = "instruct_jury"
    DELIBERATE = "deliberate"
    EVALUATE = "evaluate"
    COACH = "coach"


class EvidenceAdmissionStatus(StrEnum):
    NOT_OFFERED = "not_offered"
    OFFERED = "offered"
    ADMITTED = "admitted"
    EXCLUDED = "excluded"


class ObjectionStatus(StrEnum):
    NONE = "none"
    PENDING = "pending"
    RULED = "ruled"


class RulingOutcome(StrEnum):
    SUSTAINED = "sustained"
    OVERRULED = "overruled"
    REPHRASE = "rephrase"


class AnswerValidationStatus(StrEnum):
    SUPPORTED = "supported"
    INTENTIONAL_CONTRADICTION = "intentional_contradiction"
    HALLUCINATION = "hallucination"


class EvidenceAdmissionRecord(DomainModel):
    evidence_id: EvidenceId
    status: EvidenceAdmissionStatus = EvidenceAdmissionStatus.NOT_OFFERED
    offered_by_actor_id: ActorId | None = None
    ruling_event_id: UUID | None = None


class ObjectionRecord(DomainModel):
    objection_id: str
    status: ObjectionStatus = ObjectionStatus.PENDING
    objecting_actor_id: ActorId
    target_actor_id: ActorId | None = None
    target_evidence_id: EvidenceId | None = None
    grounds: str


class RulingRecord(DomainModel):
    ruling_id: str
    objection_id: str | None = None
    judge_actor_id: ActorId
    outcome: RulingOutcome
    explanation: str
    evidence_id: EvidenceId | None = None


class AllowedActionRule(DomainModel):
    role: str
    phase: TrialPhase | None = None
    node_purpose: str | None = None
    action_types: tuple[ActionType, ...]


class ProcedureValidationResult(DomainModel):
    valid: bool
    action_type: ActionType
    reason: str = ""


class PhaseTransitionRecord(DomainModel):
    from_phase: TrialPhase
    to_phase: TrialPhase
    reason: str


class ProcedureState(DomainModel):
    phase: TrialPhase = TrialPhase.INITIALIZATION
    active_actor_id: ActorId | None = None
    current_witness_id: WitnessId | None = None
    examination_mode: ExaminationMode | None = None
    evidence_admissions: tuple[EvidenceAdmissionRecord, ...] = ()
    pending_objection: ObjectionRecord | None = None
    rulings: tuple[RulingRecord, ...] = ()
    transitions: tuple[PhaseTransitionRecord, ...] = ()

    @property
    def admitted_evidence_ids(self) -> tuple[EvidenceId, ...]:
        return tuple(
            record.evidence_id
            for record in self.evidence_admissions
            if record.status == EvidenceAdmissionStatus.ADMITTED
        )
