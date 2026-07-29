from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.evaluation import RecordCitation
from courtroom_engine.domain.ids import ElementId, EvidenceId, FactId, MatterId, WitnessId

DELIBERATION_VERSION = "deliberation-v1"


class FindingStatus(StrEnum):
    PROVED = "proved"
    NOT_PROVED = "not_proved"
    UNRESOLVED = "unresolved"


class VerdictOutcome(StrEnum):
    PLAINTIFF = "plaintiff"
    DEFENSE = "defense"
    GUILTY = "guilty"
    NOT_GUILTY = "not_guilty"
    INVALID = "invalid"


class VerdictValidationCode(StrEnum):
    MISSING_ELEMENT_FINDING = "missing_element_finding"
    BURDEN_MISMATCH = "burden_mismatch"
    UNSUPPORTED_DISPOSITIVE_FINDING = "unsupported_dispositive_finding"
    EXCLUDED_EVIDENCE_RELIANCE = "excluded_evidence_reliance"
    UNRESOLVED_LEGAL_QUESTION = "unresolved_legal_question"
    INVALID_VERDICT_OPTION = "invalid_verdict_option"
    HIDDEN_RECORD_RELIANCE = "hidden_record_reliance"


class JudgeRecord(DomainModel):
    record_id: str
    case_id: str
    admitted_evidence_ids: tuple[EvidenceId, ...] = ()
    admitted_fact_ids: tuple[FactId, ...] = ()
    testimony_event_ids: tuple[str, ...] = ()
    admitted_knowledge_atom_ids: tuple[str, ...] = ()
    ruling_ids: tuple[str, ...] = ()
    permitted_argument_event_ids: tuple[str, ...] = ()
    excluded_object_ids: tuple[str, ...] = ()
    policy_version: str = "judge-record-v1"


class LegalQuestion(DomainModel):
    question_id: str
    matter_id: MatterId
    element_ids: tuple[ElementId, ...]
    burden_holder: PartySide
    standard: str
    verdict_options: tuple[VerdictOutcome, ...]


class ElementEvaluation(DomainModel):
    element_id: ElementId
    matter_id: MatterId
    burden_holder: PartySide
    standard: str
    supporting_citations: tuple[RecordCitation, ...] = ()
    contrary_citations: tuple[RecordCitation, ...] = ()
    unresolved_gaps: tuple[str, ...] = ()
    status: FindingStatus = FindingStatus.UNRESOLVED
    confidence: float = Field(ge=0, le=1)


class WitnessCredibilityFinding(DomainModel):
    witness_id: WitnessId
    finding_id: str
    summary: str
    supporting_citations: tuple[RecordCitation, ...]
    contradiction_citations: tuple[RecordCitation, ...] = ()
    confidence: float = Field(ge=0, le=1)


class BurdenApplication(DomainModel):
    application_id: str
    element_id: ElementId
    matter_id: MatterId
    burden_holder: PartySide
    standard: str
    element_status: FindingStatus
    conclusion: str
    citations: tuple[RecordCitation, ...]


class CandidateFinding(DomainModel):
    finding_id: str
    matter_id: MatterId
    element_id: ElementId
    status: FindingStatus
    explanation: str
    citations: tuple[RecordCitation, ...]
    challenged: bool = False
    challenge_messages: tuple[str, ...] = ()


class Verdict(DomainModel):
    verdict_id: str
    outcome: VerdictOutcome
    matter_id: MatterId
    explanation: str
    finding_ids: tuple[str, ...]
    citations: tuple[RecordCitation, ...]


class VerdictValidationIssue(DomainModel):
    code: VerdictValidationCode
    message: str
    citations: tuple[RecordCitation, ...] = ()


class VerdictValidationResult(DomainModel):
    valid: bool
    issues: tuple[VerdictValidationIssue, ...] = ()


class DeliberationReport(DomainModel):
    report_id: str
    judge_record: JudgeRecord
    legal_questions: tuple[LegalQuestion, ...]
    element_evaluations: tuple[ElementEvaluation, ...]
    credibility_findings: tuple[WitnessCredibilityFinding, ...]
    burden_applications: tuple[BurdenApplication, ...]
    candidate_findings: tuple[CandidateFinding, ...]
    finalized_findings: tuple[CandidateFinding, ...]
    verdict: Verdict
    validation: VerdictValidationResult
    deliberation_version: str = DELIBERATION_VERSION
    trial_judge_role: Literal["trial_judge"] = "trial_judge"
