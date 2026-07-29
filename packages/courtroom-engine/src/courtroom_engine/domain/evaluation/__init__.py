from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import ActorRole, PartySide
from courtroom_engine.domain.ids import ActorId, EvidenceId, FactId, ObjectiveId

EVALUATOR_VERSION = "evaluation-v1"


class CitationKind(StrEnum):
    FACT = "fact"
    EVIDENCE = "evidence"
    TRANSCRIPT_EVENT = "transcript_event"
    COURTROOM_EVENT = "courtroom_event"
    STRATEGY_OBJECTIVE = "strategy_objective"
    TACTICAL_ACTION = "tactical_action"
    RULING = "ruling"
    CONTRADICTION = "contradiction"
    ELEMENT = "element"
    FINDING = "finding"
    VERDICT = "verdict"
    KNOWLEDGE_ATOM = "knowledge_atom"


class EvaluationSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvaluationDimension(StrEnum):
    STRUCTURAL_VALIDITY = "structural_validity"
    LEGAL_GROUNDING = "legal_grounding"
    THEORY_COHERENCE = "theory_coherence"
    ELEMENT_COVERAGE = "element_coverage"
    OBJECTIVE_SELECTION = "objective_selection"
    WITNESS_SEQUENCING = "witness_sequencing"
    EVIDENCE_USE = "evidence_use"
    FOUNDATION = "foundation"
    CONTRADICTION_HANDLING = "contradiction_handling"
    OBJECTIONS = "objections"
    ADAPTATION = "adaptation"
    OPENING = "opening"
    CLOSING = "closing"
    PROCEDURE = "procedure"
    ROLE_ADHERENCE = "role_adherence"
    PROFESSIONAL_CONDUCT = "professional_conduct"
    WITNESS_SIMULATION = "witness_simulation"
    JUDICIAL_REASONING = "judicial_reasoning"
    VERDICT_SUPPORT = "verdict_support"
    SIMULATION_QUALITY = "simulation_quality"
    COACHING_OPPORTUNITY = "coaching_opportunity"


class ObservationDefectType(StrEnum):
    STRUCTURAL_INVALIDITY = "structural_invalidity"
    LEGAL_GROUNDING_PROBLEM = "legal_grounding_problem"
    STRATEGIC_MISTAKE = "strategic_mistake"
    EXECUTION_PROBLEM = "execution_problem"
    WITNESS_SIMULATION_DEFECT = "witness_simulation_defect"
    JUDGE_REASONING_DEFECT = "judge_reasoning_defect"
    COACHING_OPPORTUNITY = "coaching_opportunity"


class DeterministicCheckCode(StrEnum):
    HIDDEN_INFORMATION_LEAK = "hidden_information_leak"
    NONEXISTENT_EVIDENCE_CITED = "nonexistent_evidence_cited"
    EXCLUDED_EVIDENCE_USED = "excluded_evidence_used"
    INVALID_PHASE_TRANSITION = "invalid_phase_transition"
    UNRESOLVED_OBJECTION = "unresolved_objection"
    OUT_OF_TURN_ACTION = "out_of_turn_action"
    UNSUPPORTED_TRANSCRIPT_FACT = "unsupported_transcript_fact"
    ROLE_BOUNDARY_VIOLATION = "role_boundary_violation"
    UNSUPPORTED_VERDICT_FINDING = "unsupported_verdict_finding"


class RecordCitation(DomainModel):
    kind: CitationKind
    record_id: str
    note: str = ""


class DeterministicCheckResult(DomainModel):
    code: DeterministicCheckCode
    passed: bool
    message: str
    citations: tuple[RecordCitation, ...] = ()
    severity: EvaluationSeverity = EvaluationSeverity.HIGH


class EvaluationObservation(DomainModel):
    observation_id: str
    evaluated_actor_id: ActorId | None = None
    evaluated_role: ActorRole | None = None
    evaluated_side: PartySide | None = None
    dimension: EvaluationDimension
    defect_type: ObservationDefectType
    claim: str
    severity: EvaluationSeverity
    score_impact: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    citations: tuple[RecordCitation, ...]
    affected_objective_ids: tuple[ObjectiveId, ...] = ()
    recommended_alternative: str | None = None
    evaluator_version: str = EVALUATOR_VERSION
    review_status: Literal["machine_validated", "needs_review", "expert_reviewed"] = (
        "machine_validated"
    )

    @property
    def is_grounded(self) -> bool:
        return bool(self.citations)


class ActorEvaluation(DomainModel):
    evaluator_id: str
    evaluated_actor_id: ActorId | None = None
    evaluated_role: ActorRole | None = None
    evaluated_side: PartySide | None = None
    dimensions: tuple[EvaluationDimension, ...]
    observations: tuple[EvaluationObservation, ...] = ()
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    rubric_version: str = "rubric-v1"
    prompt_version: str = "deterministic"
    model_version: str = "deterministic"
    input_context_policy_version: str = "record-grounded-v1"
    abstention_status: Literal["answered", "abstained"] = "answered"
    human_review_status: Literal["not_required", "needs_review", "reviewed"] = (
        "not_required"
    )


class MissedOpportunity(DomainModel):
    opportunity_id: str
    actor_id: ActorId | None = None
    side: PartySide | None = None
    moment_event_id: str
    reason: str
    available_fact_ids: tuple[FactId, ...] = ()
    available_evidence_ids: tuple[EvidenceId, ...] = ()
    objective_id: ObjectiveId | None = None
    citations: tuple[RecordCitation, ...]
    severity: EvaluationSeverity
    confidence: float = Field(ge=0, le=1)
    evaluator_version: str = EVALUATOR_VERSION


class CounterfactualComparison(DomainModel):
    comparison_id: str
    opportunity_id: str
    actual_action: str
    preferred_action: str
    rejected_alternatives: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    citations: tuple[RecordCitation, ...]
    expected_value_delta: float = Field(ge=-1, le=1)
    risk_analysis: str
    confidence: float = Field(ge=0, le=1)
    evaluator_version: str = EVALUATOR_VERSION


class EvaluationAggregation(DomainModel):
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    deterministic_failures: tuple[DeterministicCheckResult, ...] = ()
    observation_ids: tuple[str, ...] = ()
    expert_review_required: bool = False


class EvaluationReport(DomainModel):
    report_id: str
    deterministic_checks: tuple[DeterministicCheckResult, ...]
    actor_evaluations: tuple[ActorEvaluation, ...]
    simulation_evaluation: ActorEvaluation
    observations: tuple[EvaluationObservation, ...]
    missed_opportunities: tuple[MissedOpportunity, ...] = ()
    counterfactual_comparisons: tuple[CounterfactualComparison, ...] = ()
    aggregation: EvaluationAggregation
    calibration_record: str
    evaluator_version: str = EVALUATOR_VERSION

    @property
    def deterministic_validation_passed(self) -> bool:
        return all(check.passed for check in self.deterministic_checks)
