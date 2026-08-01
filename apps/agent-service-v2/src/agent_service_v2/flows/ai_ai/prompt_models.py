from __future__ import annotations

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.coaching import CoachingSkill
from courtroom_engine.domain.deliberation import FindingStatus, VerdictOutcome
from courtroom_engine.domain.evaluation import (
    CitationKind,
    EvaluationDimension,
    EvaluationSeverity,
    ObservationDefectType,
)
from courtroom_engine.domain.procedure import AnswerValidationStatus
from courtroom_engine.domain.strategy import ObjectiveStatus


class CasePositionAssessment(DomainModel):
    summary: str
    target_fact_ids: tuple[str, ...] = ()
    dangerous_fact_ids: tuple[str, ...] = ()


class ElementIntelligence(DomainModel):
    element_id: str
    requirement: str
    supporting_fact_ids: tuple[str, ...] = ()
    undermining_fact_ids: tuple[str, ...] = ()
    proof_dependencies: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()


class FactProofPath(DomainModel):
    fact_id: str
    witness_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    statement_ids: tuple[str, ...] = ()
    inference_notes: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()


class CompetingFactualInterpretation(DomainModel):
    issue: str
    plaintiff_interpretation: str
    defense_interpretation: str
    related_fact_ids: tuple[str, ...] = ()


class StrategicOpportunity(DomainModel):
    side: PartySide
    description: str
    related_element_ids: tuple[str, ...] = ()
    related_fact_ids: tuple[str, ...] = ()


class CaseIntelligenceAnalysis(DomainModel):
    summary: str
    elements: tuple[ElementIntelligence, ...] = ()
    proof_paths: tuple[FactProofPath, ...] = ()
    competing_interpretations: tuple[CompetingFactualInterpretation, ...] = ()
    strategic_opportunities: tuple[StrategicOpportunity, ...] = ()


class CaseTheoryPlan(DomainModel):
    theme: str
    core_claim: str
    target_element_ids: tuple[str, ...] = ()
    supporting_fact_ids: tuple[str, ...] = ()
    dangerous_fact_ids: tuple[str, ...] = ()


class StrategicObjectiveItem(DomainModel):
    objective_id: str
    description: str
    target_element_ids: tuple[str, ...] = ()
    target_fact_ids: tuple[str, ...] = ()
    priority: float
    success_signals: tuple[str, ...] = ()
    failure_signals: tuple[str, ...] = ()


class StrategicObjectivePlan(DomainModel):
    objectives: tuple[StrategicObjectiveItem, ...]


class WitnessUsageEntry(DomainModel):
    witness_id: str
    objective_ids: tuple[str, ...] = ()
    direct_topics: tuple[str, ...] = ()
    cross_risks: tuple[str, ...] = ()
    order: int
    omit: bool = False


class WitnessUsagePlan(DomainModel):
    witness_plans: tuple[WitnessUsageEntry, ...]


class EvidenceUsageEntry(DomainModel):
    evidence_id: str
    objective_ids: tuple[str, ...] = ()
    fact_ids: tuple[str, ...] = ()
    through_witness_id: str | None = None
    foundation_required: bool = True
    expected_objections: tuple[str, ...] = ()
    fallback: str = ""


class EvidenceUsagePlan(DomainModel):
    evidence_plans: tuple[EvidenceUsageEntry, ...]


class OpponentRiskItem(DomainModel):
    risk_id: str
    description: str
    related_fact_ids: tuple[str, ...] = ()
    related_evidence_ids: tuple[str, ...] = ()
    severity: float


class OpponentModel(DomainModel):
    opponent_risks: tuple[OpponentRiskItem, ...]


class RankedStrategyPlan(DomainModel):
    summary: str
    preferred_objective_ids: tuple[str, ...] = ()


class StrategyReview(DomainModel):
    approved: bool
    messages: tuple[str, ...] = ()
    invalid_references: tuple[str, ...] = ()


class OpeningPlan(DomainModel):
    themes: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    concessions: tuple[str, ...] = ()
    requested_outcome: str


class SpokenOpening(DomainModel):
    text: str


class OpeningCommitment(DomainModel):
    commitment_id: str
    text: str
    related_fact_ids: tuple[str, ...] = ()


class OpeningCommitmentSet(DomainModel):
    commitments: tuple[OpeningCommitment, ...]


class OpeningReview(DomainModel):
    approved: bool
    messages: tuple[str, ...] = ()


class WitnessSelectionDecision(DomainModel):
    witness_id: str | None = None
    calling_side: PartySide | None = None
    strategy_key: str | None = None
    objective_ids: tuple[str, ...] = ()
    reason: str
    end_phase: bool = False


class ExaminationObjectiveDecision(DomainModel):
    objective_id: str
    reason: str


class PlannedExaminationAction(DomainModel):
    action_id: str
    objective_id: str
    action_type: str
    target_fact_ids: tuple[str, ...] = ()
    target_evidence_ids: tuple[str, ...] = ()
    target_witness_id: str | None = None
    expected_effect: str


class ExaminationActionReview(DomainModel):
    approved: bool
    messages: tuple[str, ...] = ()


class GeneratedQuestion(DomainModel):
    question_text: str
    goal: str


class ProceduralChallengeDecision(DomainModel):
    challenge: bool
    ground: str = ""
    reason: str


class ProceduralDecision(DomainModel):
    outcome: str
    rationale: str


class WitnessAnswer(DomainModel):
    answer_text: str


class WitnessAnswerReview(DomainModel):
    status: AnswerValidationStatus
    message: str


class RuntimeContradictionResult(DomainModel):
    contradiction_ids: tuple[str, ...] = ()
    summary: str


class ObjectiveProgressAssessment(DomainModel):
    next_step: str
    objective_status: ObjectiveStatus
    reason: str


class PartyTrialPositionPatch(DomainModel):
    completed_objective_ids: tuple[str, ...] = ()
    admitted_evidence_ids: tuple[str, ...] = ()
    summary: str


class WitnessResult(DomainModel):
    summary: str
    established_fact_ids: tuple[str, ...] = ()
    weakened_fact_ids: tuple[str, ...] = ()
    unresolved_fact_ids: tuple[str, ...] = ()


class ClosingRecordPrompt(DomainModel):
    admitted_evidence_ids: tuple[str, ...] = ()
    testimony_event_ids: tuple[str, ...] = ()
    completed_objective_ids: tuple[str, ...] = ()
    unresolved_contradiction_ids: tuple[str, ...] = ()
    opening_commitments: tuple[str, ...] = ()


class ClosingPositionAssessment(DomainModel):
    strongest_conclusions: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    responses: tuple[str, ...] = ()


class ClosingPlan(DomainModel):
    key_points: tuple[str, ...] = ()
    requested_outcome: str


class SpokenClosing(DomainModel):
    text: str


class ClosingReview(DomainModel):
    approved: bool
    messages: tuple[str, ...] = ()


class DecisionQuestion(DomainModel):
    question_id: str
    matter_id: str
    element_ids: tuple[str, ...] = ()
    burden_holder: PartySide
    standard: str
    verdict_options: tuple[VerdictOutcome, ...]


class DecisionQuestionSet(DomainModel):
    questions: tuple[DecisionQuestion, ...]


class FactFinding(DomainModel):
    finding_id: str
    matter_id: str
    element_id: str
    status: FindingStatus
    explanation: str
    citation_record_ids: tuple[str, ...] = ()


class FactFinderDeliberationResult(DomainModel):
    provisional_findings: tuple[FactFinding, ...]
    summary: str


class ElementEvaluationItem(DomainModel):
    element_id: str
    matter_id: str
    burden_holder: PartySide
    standard: str
    supporting_record_ids: tuple[str, ...] = ()
    contrary_record_ids: tuple[str, ...] = ()
    unresolved_gaps: tuple[str, ...] = ()
    status: FindingStatus
    confidence: float


class ElementEvaluationSet(DomainModel):
    evaluations: tuple[ElementEvaluationItem, ...]


class WitnessCredibilityAssessment(DomainModel):
    witness_id: str
    finding_id: str
    summary: str
    supporting_record_ids: tuple[str, ...] = ()
    contradiction_record_ids: tuple[str, ...] = ()
    confidence: float


class WitnessCredibilityAssessmentSet(DomainModel):
    assessments: tuple[WitnessCredibilityAssessment, ...]


class BurdenApplicationItem(DomainModel):
    application_id: str
    element_id: str
    matter_id: str
    burden_holder: PartySide
    standard: str
    element_status: FindingStatus
    conclusion: str
    citation_record_ids: tuple[str, ...] = ()


class BurdenApplicationResult(DomainModel):
    applications: tuple[BurdenApplicationItem, ...]


class CandidateFindings(DomainModel):
    findings: tuple[FactFinding, ...]
    verdict_outcome: VerdictOutcome
    verdict_explanation: str
    verdict_citation_record_ids: tuple[str, ...] = ()


class FindingsChallenge(DomainModel):
    approved: bool
    messages: tuple[str, ...] = ()
    challenged_finding_ids: tuple[str, ...] = ()


class FinalDecision(DomainModel):
    matter_id: str
    verdict_outcome: VerdictOutcome
    explanation: str
    finding_ids: tuple[str, ...] = ()
    citation_record_ids: tuple[str, ...] = ()


class FinalDecisionReview(DomainModel):
    approved: bool
    messages: tuple[str, ...] = ()


class EvaluationObservationInput(DomainModel):
    dimension: EvaluationDimension
    defect_type: ObservationDefectType
    claim: str
    severity: EvaluationSeverity
    score_impact: float
    confidence: float
    citation_record_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()


class PartyAdvocacyEvaluation(DomainModel):
    side: PartySide
    observations: tuple[EvaluationObservationInput, ...] = ()
    score: float
    confidence: float


class WitnessSimulationEvaluation(DomainModel):
    witness_id: str
    observations: tuple[EvaluationObservationInput, ...] = ()
    score: float
    confidence: float


class ProceduralDecisionEvaluation(DomainModel):
    observations: tuple[EvaluationObservationInput, ...] = ()
    score: float
    confidence: float


class FactFinderEvaluation(DomainModel):
    observations: tuple[EvaluationObservationInput, ...] = ()
    score: float
    confidence: float


class SimulationQualityEvaluation(DomainModel):
    observations: tuple[EvaluationObservationInput, ...] = ()
    score: float
    confidence: float


class MissedOpportunityItem(DomainModel):
    opportunity_id: str
    actor_id: str | None = None
    side: PartySide | None = None
    moment_event_id: str
    reason: str
    available_fact_ids: tuple[str, ...] = ()
    available_evidence_ids: tuple[str, ...] = ()
    objective_id: str | None = None
    citation_record_ids: tuple[str, ...] = ()
    severity: EvaluationSeverity
    confidence: float


class MissedOpportunitySet(DomainModel):
    opportunities: tuple[MissedOpportunityItem, ...] = ()


class CounterfactualActionItem(DomainModel):
    comparison_id: str
    opportunity_id: str
    actual_action: str
    preferred_action: str
    rejected_alternatives: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    citation_record_ids: tuple[str, ...] = ()
    expected_value_delta: float
    risk_analysis: str
    confidence: float


class CounterfactualActionComparison(DomainModel):
    comparisons: tuple[CounterfactualActionItem, ...] = ()


class EvaluationCalibration(DomainModel):
    summary: str
    score: float
    confidence: float
    expert_review_required: bool = False


class LearningMomentSelection(DomainModel):
    observation_ids: tuple[str, ...] = ()


class CausalMoment(DomainModel):
    observation_id: str
    transcript_location: str
    skill: CoachingSkill
    what_happened: str
    why_it_mattered: str
    better_action: str
    example_wording: str
    expected_response: str
    recovery_option: str
    severity: str
    confidence: float
    objective_ids: tuple[str, ...] = ()
    citation_record_ids: tuple[str, ...] = ()


class CausalCoachingFeedback(DomainModel):
    moments: tuple[CausalMoment, ...] = ()


class BetterActionSequenceOutput(DomainModel):
    observation_id: str
    steps: tuple[str, ...] = ()
    citation_record_ids: tuple[str, ...] = ()


class BetterActionSequenceSet(DomainModel):
    sequences: tuple[BetterActionSequenceOutput, ...] = ()


class ExampleExecutionItem(DomainModel):
    observation_id: str
    wording: str


class ExampleExecution(DomainModel):
    examples: tuple[ExampleExecutionItem, ...] = ()


class SkillProfileUpdateInput(DomainModel):
    actor_id: str | None = None
    role: str | None = None
    skill: CoachingSkill
    direction: str
    strength: float
    confidence: float
    citation_record_ids: tuple[str, ...] = ()
    source_observation_id: str


class LearnerImprovementPlan(DomainModel):
    steps: tuple[str, ...] = ()
    skill_updates: tuple[SkillProfileUpdateInput, ...] = ()
