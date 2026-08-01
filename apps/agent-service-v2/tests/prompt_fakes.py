from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.coaching import CoachingSkill
from courtroom_engine.domain.deliberation import FindingStatus, VerdictOutcome
from courtroom_engine.domain.evaluation import (
    EvaluationDimension,
    EvaluationSeverity,
    ObservationDefectType,
)
from courtroom_engine.domain.procedure import AnswerValidationStatus
from courtroom_engine.domain.strategy import ObjectiveStatus

from agent_service_v2.prompts import PromptId
from agent_service_v2.shared import InvocationOutcome, PromptInvocationResult, PromptUsage
from agent_service_v2.flows.ai_ai.prompt_models import (
    BetterActionSequenceOutput,
    BetterActionSequenceSet,
    BurdenApplicationItem,
    BurdenApplicationResult,
    CandidateFindings,
    CaseIntelligenceAnalysis,
    CasePositionAssessment,
    CaseTheoryPlan,
    CausalCoachingFeedback,
    CausalMoment,
    ClosingPlan,
    ClosingPositionAssessment,
    ClosingRecordPrompt,
    ClosingReview,
    CounterfactualActionComparison,
    CounterfactualActionItem,
    DecisionQuestion,
    DecisionQuestionSet,
    ElementEvaluationItem,
    ElementEvaluationSet,
    EvaluationCalibration,
    EvaluationObservationInput,
    ExampleExecution,
    ExampleExecutionItem,
    ExaminationActionReview,
    ExaminationObjectiveDecision,
    FactFinding,
    FactFinderDeliberationResult,
    FactFinderEvaluation,
    FinalDecision,
    FinalDecisionReview,
    FindingsChallenge,
    GeneratedQuestion,
    LearnerImprovementPlan,
    LearningMomentSelection,
    MissedOpportunityItem,
    MissedOpportunitySet,
    ObjectiveProgressAssessment,
    OpeningCommitment,
    OpeningCommitmentSet,
    OpeningPlan,
    OpeningReview,
    OpponentModel,
    OpponentRiskItem,
    PartyAdvocacyEvaluation,
    PartyTrialPositionPatch,
    PlannedExaminationAction,
    ProceduralChallengeDecision,
    ProceduralDecision,
    ProceduralDecisionEvaluation,
    RankedStrategyPlan,
    RuntimeContradictionResult,
    SimulationQualityEvaluation,
    SkillProfileUpdateInput,
    SpokenClosing,
    SpokenOpening,
    StrategicObjectiveItem,
    StrategicObjectivePlan,
    StrategyReview,
    WitnessAnswer,
    WitnessAnswerReview,
    WitnessCredibilityAssessment,
    WitnessCredibilityAssessmentSet,
    WitnessResult,
    WitnessSelectionDecision,
    WitnessSimulationEvaluation,
    WitnessUsageEntry,
    WitnessUsagePlan,
    EvidenceUsageEntry,
    EvidenceUsagePlan,
)


@dataclass
class CannedPromptExecutor:
    calls: list[str] = field(default_factory=list)

    def invoke(
        self,
        *,
        prompt_id: PromptId | str,
        context: Any,
        schema: type[Any],
        semantic_validator: Any = None,
        metadata: Mapping[str, str] | None = None,
        cache_scope: str | None = None,
        max_output_tokens: int | None = None,
    ) -> PromptInvocationResult[Any]:
        resolved = PromptId(prompt_id)
        self.calls.append(resolved.value)
        output = self._build_output(resolved, context, schema)
        if semantic_validator is not None:
            validation = semantic_validator(output)
            if not validation.accepted:
                raise AssertionError(
                    f"Canned output failed semantic validation for {resolved.value}: "
                    f"{validation.error_message}"
                )
        return PromptInvocationResult(
            output=output,
            outcome=InvocationOutcome.SUCCESS,
            usage=PromptUsage(),
            attempts=1,
            response_id=f"resp_{resolved.value}",
        )

    def _build_output(self, prompt_id: PromptId, context: Any, schema: type[Any]) -> Any:
        if prompt_id is PromptId.ANALYZE_CASE_INTELLIGENCE:
            return CaseIntelligenceAnalysis(
                summary="Case intelligence identifies available proof and vulnerabilities.",
            )
        if prompt_id is PromptId.ASSESS_CASE_POSITION:
            return CasePositionAssessment(
                summary=f"{context['side'].value} position assessed from visible proof.",
                target_fact_ids=tuple(f.fact_id for f in context["case_package"].facts),
            )
        if prompt_id is PromptId.DEVELOP_CASE_THEORY:
            matter = context["case_package"].matters[0]
            return CaseTheoryPlan(
                theme=f"{context['side'].value.title()} theory",
                core_claim="Use the visible record to prove the central matter.",
                target_element_ids=tuple(element.element_id for element in matter.elements),
                supporting_fact_ids=tuple(f.fact_id for f in context["case_package"].facts),
            )
        if prompt_id is PromptId.GENERATE_STRATEGIC_OBJECTIVES:
            matter = context["case_package"].matters[0]
            return StrategicObjectivePlan(
                objectives=(
                    StrategicObjectiveItem(
                        objective_id=f"OBJ-{context['side'].value.upper()}-001",
                        description="Establish the decisive visible fact.",
                        target_element_ids=tuple(element.element_id for element in matter.elements),
                        target_fact_ids=tuple(f.fact_id for f in context["case_package"].facts[:1]),
                        priority=0.8,
                        success_signals=("Record supports the decisive fact.",),
                        failure_signals=("The decisive fact remains weak.",),
                    ),
                )
            )
        if prompt_id is PromptId.PLAN_WITNESS_USAGE:
            witnesses = [
                witness
                for witness in context["case_package"].witnesses
                if witness.called_by == context["side"]
            ]
            return WitnessUsagePlan(
                witness_plans=tuple(
                    WitnessUsageEntry(
                        witness_id=witness.witness_id,
                        objective_ids=tuple(
                            item.objective_id for item in context["objectives"].objectives
                        ),
                        direct_topics=(witness.public_summary,),
                        order=index + 1,
                    )
                    for index, witness in enumerate(witnesses)
                )
            )
        if prompt_id is PromptId.PLAN_EVIDENCE_USAGE:
            evidence = [
                item
                for item in context["case_package"].evidence
                if item.offered_by == context["side"]
            ]
            through_witness_id = (
                context["case_package"].witnesses[0].witness_id
                if context["case_package"].witnesses
                else None
            )
            return EvidenceUsagePlan(
                evidence_plans=tuple(
                    EvidenceUsageEntry(
                        evidence_id=item.evidence_id,
                        objective_ids=tuple(
                            objective.objective_id for objective in context["objectives"].objectives
                        ),
                        fact_ids=item.supports_fact_ids,
                        through_witness_id=through_witness_id,
                        expected_objections=("foundation",),
                        fallback="Use witness testimony to authenticate the exhibit.",
                    )
                    for item in evidence
                )
            )
        if prompt_id is PromptId.ANTICIPATE_OPPONENT:
            return OpponentModel(
                opponent_risks=(
                    OpponentRiskItem(
                        risk_id=f"RSK-{context['side'].value.upper()}-001",
                        description="Opponent will attack notice and foundation.",
                        severity=0.5,
                    ),
                )
            )
        if prompt_id is PromptId.RANK_STRATEGY:
            return RankedStrategyPlan(summary="Prioritize the strongest visible proof.")
        if prompt_id is PromptId.REVIEW_STRATEGY:
            return StrategyReview(approved=True, messages=("Strategy is coherent.",))
        if prompt_id is PromptId.PLAN_OPENING:
            return OpeningPlan(
                themes=("Visible proof establishes the claim.",),
                objective_ids=tuple(obj.objective_id for obj in context["strategy"].objectives),
                evidence_ids=tuple(item.evidence_id for item in context["strategy"].evidence_plans),
                requested_outcome=f"Find for the {context['side'].value}.",
            )
        if prompt_id is PromptId.DRAFT_OPENING:
            return SpokenOpening(text=f"{context['side'].value.title()} opening based on the approved plan.")
        if prompt_id is PromptId.EXTRACT_OPENING_COMMITMENTS:
            return OpeningCommitmentSet(
                commitments=(
                    OpeningCommitment(
                        commitment_id=f"COM-{context['side'].value.upper()}-001",
                        text=f"{context['side'].value.title()} will prove the central fact.",
                    ),
                )
            )
        if prompt_id is PromptId.REVIEW_OPENING:
            return OpeningReview(approved=True, messages=("Opening is grounded.",))
        if prompt_id is PromptId.SELECT_NEXT_WITNESS:
            first = context["remaining_witness_keys"][0]
            strategy_key, witness_id = first.split(":", 1)
            side = context["strategies"][strategy_key].side
            return WitnessSelectionDecision(
                witness_id=witness_id,
                calling_side=side,
                strategy_key=strategy_key,
                objective_ids=tuple(
                    obj.objective_id for obj in context["strategies"][strategy_key].objectives
                ),
                reason=f"Call {witness_id} next.",
            )
        if prompt_id is PromptId.SELECT_EXAMINATION_OBJECTIVE:
            return ExaminationObjectiveDecision(
                objective_id=context["strategy"].objectives[0].objective_id,
                reason="Advance the active objective for the witness.",
            )
        if prompt_id is PromptId.PLAN_EXAMINATION_ACTION:
            objective = context["strategy"].objectives[0]
            return PlannedExaminationAction(
                action_id=f"ACT-{context['witness_id']}",
                objective_id=context["active_objective_id"],
                action_type="foundation_question",
                target_fact_ids=objective.target_fact_ids,
                target_witness_id=context["witness_id"],
                expected_effect="Elicit the core factual support.",
            )
        if prompt_id is PromptId.REVIEW_EXAMINATION_ACTION:
            return ExaminationActionReview(approved=True, messages=("Action is valid.",))
        if prompt_id is PromptId.DRAFT_QUESTION:
            target = context["question_brief"].allowed_fact_ids[0]
            return GeneratedQuestion(
                question_text=f"What can you tell the court about {target}?",
                goal=context["question_brief"].question_goal,
            )
        if prompt_id is PromptId.PROCEDURAL_CHALLENGE_DECISION:
            return ProceduralChallengeDecision(
                challenge=False,
                reason="No good-faith procedural challenge is available.",
            )
        if prompt_id is PromptId.PROCEDURAL_DECISION:
            return ProceduralDecision(outcome="overruled", rationale="No objection to sustain.")
        if prompt_id is PromptId.WITNESS_ANSWER:
            knowledge = context["witness_knowledge"][0]
            return WitnessAnswer(answer_text=knowledge.text)
        if prompt_id is PromptId.REVIEW_WITNESS_ANSWER:
            grounded = context["grounded_validation"]
            return WitnessAnswerReview(status=grounded.status, message=grounded.message)
        if prompt_id is PromptId.DETECT_RUNTIME_CONTRADICTIONS:
            validation = context["answer_validation"]
            return RuntimeContradictionResult(
                contradiction_ids=validation.contradiction_ids,
                summary="No new contradiction beyond the grounded record.",
            )
        if prompt_id is PromptId.ASSESS_OBJECTIVE_PROGRESS:
            validation = context["answer_validation"]
            status = (
                ObjectiveStatus.SATISFIED
                if validation.status != AnswerValidationStatus.HALLUCINATION
                else ObjectiveStatus.ACTIVE
            )
            return ObjectiveProgressAssessment(
                next_step="finish_section",
                objective_status=status,
                reason="The examination objective has been sufficiently advanced.",
            )
        if prompt_id is PromptId.SUMMARIZE_WITNESS_RESULT:
            return WitnessResult(summary="Witness established the central visible fact.")
        if prompt_id is PromptId.UPDATE_PARTY_TRIAL_POSITION:
            output = context["latest_witness_result"]
            evidence_ids = tuple(
                item.evidence_id
                for item in context["strategy"].evidence_plans
                if item.through_witness_id == output.witness_id
            )
            completed = (
                (output.objective_id,)
                if output.objective_status == ObjectiveStatus.SATISFIED
                else ()
            )
            return PartyTrialPositionPatch(
                completed_objective_ids=completed,
                admitted_evidence_ids=evidence_ids,
                summary=f"Updated trial position after {output.witness_id}.",
            )
        if prompt_id is PromptId.PREPARE_CLOSING_RECORD:
            runtime = context["runtime"]
            return ClosingRecordPrompt(
                admitted_evidence_ids=runtime.admitted_evidence_ids,
                testimony_event_ids=tuple(
                    str(event.event_id)
                    for event in runtime.events
                    if event.event_type == "witness_answered"
                ),
                completed_objective_ids=tuple(
                    objective_id
                    for update in context["trial_position_updates"]
                    for objective_id in update.completed_objective_ids
                ),
                opening_commitments=context["opening_commitments"],
            )
        if prompt_id is PromptId.ASSESS_CLOSING_POSITION:
            return ClosingPositionAssessment(
                strongest_conclusions=("The visible record supports the claim.",),
                weaknesses=("Foundation may be challenged.",),
                responses=("Point to admitted evidence and witness testimony.",),
            )
        if prompt_id is PromptId.PLAN_CLOSING:
            side = context["side"].value
            return ClosingPlan(
                key_points=("Apply the visible record to the controlling element.",),
                requested_outcome=f"Find for the {side}.",
            )
        if prompt_id is PromptId.DRAFT_CLOSING:
            return SpokenClosing(text=f"{context['side'].value.title()} closing from the approved plan.")
        if prompt_id is PromptId.REVIEW_CLOSING:
            return ClosingReview(approved=True, messages=("Closing is grounded.",))
        if prompt_id is PromptId.IDENTIFY_DECISION_QUESTIONS:
            matter = context["case_package"].matters[0]
            return DecisionQuestionSet(
                questions=(
                    DecisionQuestion(
                        question_id=f"Q-{matter.matter_id}",
                        matter_id=matter.matter_id,
                        element_ids=tuple(element.element_id for element in matter.elements),
                        burden_holder=matter.elements[0].proving_side,
                        standard=matter.elements[0].burden,
                        verdict_options=(VerdictOutcome.PLAINTIFF, VerdictOutcome.DEFENSE),
                    ),
                )
            )
        if prompt_id is PromptId.FACT_FINDER_DELIBERATION:
            question = context["decision_questions"].questions[0]
            return FactFinderDeliberationResult(
                provisional_findings=(
                    FactFinding(
                        finding_id=f"F-{question.element_ids[0]}",
                        matter_id=question.matter_id,
                        element_id=question.element_ids[0],
                        status=FindingStatus.PROVED,
                        explanation="The admitted evidence and testimony support the element.",
                    ),
                ),
                summary="Provisional findings support the plaintiff.",
            )
        if prompt_id is PromptId.EVALUATE_LEGAL_ELEMENTS:
            question = context["decision_questions"].questions[0]
            return ElementEvaluationSet(
                evaluations=(
                    ElementEvaluationItem(
                        element_id=question.element_ids[0],
                        matter_id=question.matter_id,
                        burden_holder=question.burden_holder,
                        standard=question.standard,
                        status=FindingStatus.PROVED,
                        confidence=0.8,
                    ),
                )
            )
        if prompt_id is PromptId.ASSESS_WITNESS_CREDIBILITY:
            witness_id = context["witness_examinations"][0].witness_id
            return WitnessCredibilityAssessmentSet(
                assessments=(
                    WitnessCredibilityAssessment(
                        witness_id=witness_id,
                        finding_id=f"CRED-{witness_id}",
                        summary="Witness remained within grounded knowledge.",
                        confidence=0.8,
                    ),
                )
            )
        if prompt_id is PromptId.APPLY_BURDEN:
            evaluation = context["element_evaluations"].evaluations[0]
            return BurdenApplicationResult(
                applications=(
                    BurdenApplicationItem(
                        application_id=f"BUR-{evaluation.element_id}",
                        element_id=evaluation.element_id,
                        matter_id=evaluation.matter_id,
                        burden_holder=evaluation.burden_holder,
                        standard=evaluation.standard,
                        element_status=evaluation.status,
                        conclusion="The burden is met.",
                    ),
                )
            )
        if prompt_id is PromptId.GENERATE_FINDINGS:
            finding = context["deliberation"].provisional_findings[0]
            return CandidateFindings(
                findings=(finding,),
                verdict_outcome=VerdictOutcome.PLAINTIFF,
                verdict_explanation="The plaintiff carried the burden on the visible record.",
            )
        if prompt_id is PromptId.CHALLENGE_FINDINGS:
            return FindingsChallenge(approved=True, messages=("Findings are supported.",))
        if prompt_id is PromptId.DRAFT_FINAL_DECISION:
            candidate = context["candidate_findings"]
            return FinalDecision(
                matter_id=candidate.findings[0].matter_id,
                verdict_outcome=candidate.verdict_outcome,
                explanation=candidate.verdict_explanation,
                finding_ids=tuple(item.finding_id for item in candidate.findings),
            )
        if prompt_id is PromptId.REVIEW_FINAL_DECISION:
            return FinalDecisionReview(approved=True, messages=("Decision is grounded.",))
        if prompt_id is PromptId.EVALUATE_PARTY_ADVOCACY:
            return PartyAdvocacyEvaluation(
                side=context["strategy"].side,
                observations=(
                    EvaluationObservationInput(
                        dimension=EvaluationDimension.OPENING,
                        defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
                        claim="The party maintained a coherent case theory.",
                        severity=EvaluationSeverity.INFO,
                        score_impact=0.2,
                        confidence=0.8,
                    ),
                ),
                score=0.75,
                confidence=0.8,
            )
        if prompt_id is PromptId.EVALUATE_WITNESS_SIMULATION:
            return WitnessSimulationEvaluation(
                witness_id=context["witness_result"].witness_id,
                observations=(
                    EvaluationObservationInput(
                        dimension=EvaluationDimension.WITNESS_SIMULATION,
                        defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
                        claim="The witness stayed within grounded knowledge.",
                        severity=EvaluationSeverity.INFO,
                        score_impact=0.1,
                        confidence=0.8,
                    ),
                ),
                score=0.8,
                confidence=0.8,
            )
        if prompt_id is PromptId.EVALUATE_PROCEDURAL_DECISIONS:
            return ProceduralDecisionEvaluation(
                observations=(
                    EvaluationObservationInput(
                        dimension=EvaluationDimension.PROCEDURE,
                        defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
                        claim="Procedural flow remained coherent.",
                        severity=EvaluationSeverity.INFO,
                        score_impact=0.1,
                        confidence=0.8,
                    ),
                ),
                score=0.8,
                confidence=0.8,
            )
        if prompt_id is PromptId.EVALUATE_FACT_FINDER:
            return FactFinderEvaluation(
                observations=(
                    EvaluationObservationInput(
                        dimension=EvaluationDimension.JUDICIAL_REASONING,
                        defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
                        claim="The fact finder tied conclusions to the record.",
                        severity=EvaluationSeverity.INFO,
                        score_impact=0.1,
                        confidence=0.8,
                    ),
                ),
                score=0.8,
                confidence=0.8,
            )
        if prompt_id is PromptId.EVALUATE_SIMULATION_QUALITY:
            return SimulationQualityEvaluation(
                observations=(
                    EvaluationObservationInput(
                        dimension=EvaluationDimension.SIMULATION_QUALITY,
                        defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
                        claim="The simulation remained procedurally coherent.",
                        severity=EvaluationSeverity.INFO,
                        score_impact=0.1,
                        confidence=0.8,
                    ),
                ),
                score=0.82,
                confidence=0.8,
            )
        if prompt_id is PromptId.DETECT_MISSED_OPPORTUNITIES:
            witness_result = context["witness_examinations"][0]
            return MissedOpportunitySet(
                opportunities=(
                    MissedOpportunityItem(
                        opportunity_id="MO-001",
                        side=PartySide.PLAINTIFF,
                        moment_event_id=str(witness_result.events[0].event_id),
                        reason="Could have tightened the foundation before introducing the exhibit.",
                        severity=EvaluationSeverity.LOW,
                        confidence=0.7,
                    ),
                )
            )
        if prompt_id is PromptId.COMPARE_COUNTERFACTUAL_ACTIONS:
            opportunity = context["missed_opportunities"].opportunities[0]
            return CounterfactualActionComparison(
                comparisons=(
                    CounterfactualActionItem(
                        comparison_id="CF-001",
                        opportunity_id=opportunity.opportunity_id,
                        actual_action="Move directly to the central fact.",
                        preferred_action="Lay one more foundation question first.",
                        expected_value_delta=0.2,
                        risk_analysis="Lower objection risk with minimal cost.",
                        confidence=0.7,
                    ),
                )
            )
        if prompt_id is PromptId.CALIBRATE_EVALUATION:
            return EvaluationCalibration(
                summary="Confidence is moderate because the record is small but internally consistent.",
                score=0.8,
                confidence=0.78,
            )
        if prompt_id is PromptId.SELECT_LEARNING_MOMENTS:
            observation_id = context["evaluation"].observations[0].observation_id
            return LearningMomentSelection(observation_ids=(observation_id,))
        if prompt_id is PromptId.GENERATE_CAUSAL_FEEDBACK:
            observation_id = context["learning_moments"].observation_ids[0]
            return CausalCoachingFeedback(
                moments=(
                    CausalMoment(
                        observation_id=observation_id,
                        transcript_location="Witness examination",
                        skill=CoachingSkill.FOUNDATION,
                        what_happened="The advocate moved efficiently but left one foundation step implicit.",
                        why_it_mattered="A stronger foundation would reduce avoidable risk.",
                        better_action="Ask one brief authentication question before the key exhibit point.",
                        example_wording="Did you recognize the camera angle from your shift?",
                        expected_response="Yes, it shows the aisle where I was working.",
                        recovery_option="If challenged, return to the authentication step.",
                        severity="low",
                        confidence=0.75,
                    ),
                )
            )
        if prompt_id is PromptId.GENERATE_BETTER_ACTION_SEQUENCE:
            observation_id = context["causal_feedback"].moments[0].observation_id
            return BetterActionSequenceSet(
                sequences=(
                    BetterActionSequenceOutput(
                        observation_id=observation_id,
                        steps=(
                            "Authenticate the witness’s vantage point.",
                            "Tie the exhibit to the witness’s observations.",
                            "Then ask the decisive factual question.",
                        ),
                    ),
                )
            )
        if prompt_id is PromptId.GENERATE_EXAMPLE_EXECUTION:
            observation_id = context["better_action_sequences"].sequences[0].observation_id
            return ExampleExecution(
                examples=(
                    ExampleExecutionItem(
                        observation_id=observation_id,
                        wording="Did you recognize the video angle from where you were working that day?",
                    ),
                )
            )
        if prompt_id is PromptId.BUILD_IMPROVEMENT_PLAN:
            observation_id = context["causal_feedback"].moments[0].observation_id
            return LearnerImprovementPlan(
                steps=("Practice laying exhibit foundation in one clean sequence.",),
                skill_updates=(
                    SkillProfileUpdateInput(
                        skill=CoachingSkill.FOUNDATION,
                        direction="positive",
                        strength=0.6,
                        confidence=0.75,
                        source_observation_id=observation_id,
                    ),
                ),
            )
        raise AssertionError(f"No canned output configured for {prompt_id.value} / {schema.__name__}")
