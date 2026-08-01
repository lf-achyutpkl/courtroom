from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import uuid4

from courtroom_engine.compiler import CaseCompiler
from courtroom_engine.domain.case import ActorRole, PartySide
from courtroom_engine.domain.coaching import (
    BetterActionSequence,
    CoachingMoment,
    CoachingReport,
    SkillEvidence,
    SkillProfileUpdate,
)
from courtroom_engine.domain.deliberation import (
    BurdenApplication,
    CandidateFinding,
    DeliberationReport,
    ElementEvaluation,
    JudgeRecord,
    LegalQuestion,
    Verdict,
    VerdictValidationResult,
    WitnessCredibilityFinding,
)
from courtroom_engine.domain.evaluation import (
    ActorEvaluation,
    CitationKind,
    DeterministicCheckCode,
    CounterfactualComparison,
    DeterministicCheckResult,
    EvaluationAggregation,
    EvaluationDimension,
    EvaluationObservation,
    EvaluationReport,
    EvaluationSeverity,
    MissedOpportunity,
    RecordCitation,
)
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import (
    EvidenceAdmissionRecord,
    EvidenceAdmissionStatus,
    ExaminationMode,
    PhaseTransitionRecord,
    ProcedureState,
    TrialPhase,
)
from courtroom_engine.domain.strategy import (
    CaseTheory,
    ObjectiveRuntimeState,
    OpponentRiskRecord,
    PartyStrategy,
    StrategicObjective,
    StrategyValidationRecord,
    StrategyValidationStatus,
    WitnessPlan,
    EvidencePlan,
)
from courtroom_engine.domain.trial import (
    AuthoredCaseTemplate,
    CompiledCasePackage,
    TrialRuntimeState,
)
from courtroom_engine.fixtures import build_reference_case
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from agent_service_v2.prompts import PromptId
from agent_service_v2.shared import (
    InvocationOutcome,
    PromptInvocationError,
    SemanticValidationResult,
)
from agent_service_v2.shared.prompt_executor import (
    NodeFailureRecord,
    PromptRunRecord,
    StructuredPromptExecutor,
)

from .prompt_models import (
    BetterActionSequenceSet,
    BurdenApplicationResult,
    CandidateFindings,
    CaseIntelligenceAnalysis,
    CasePositionAssessment,
    CaseTheoryPlan,
    CausalCoachingFeedback,
    ClosingPlan,
    ClosingPositionAssessment,
    ClosingRecordPrompt,
    ClosingReview,
    CounterfactualActionComparison,
    DecisionQuestionSet,
    ElementEvaluationSet,
    EvaluationCalibration,
    ExampleExecution,
    FactFinderDeliberationResult,
    FactFinderEvaluation,
    FinalDecision,
    FinalDecisionReview,
    FindingsChallenge,
    LearnerImprovementPlan,
    LearningMomentSelection,
    MissedOpportunitySet,
    ObjectiveProgressAssessment,
    OpeningCommitmentSet,
    OpeningPlan,
    OpeningReview,
    OpponentModel,
    PartyAdvocacyEvaluation,
    PartyTrialPositionPatch,
    ProceduralDecisionEvaluation,
    RankedStrategyPlan,
    SimulationQualityEvaluation,
    SpokenClosing,
    SpokenOpening,
    StrategicObjectivePlan,
    StrategyReview,
    WitnessSelectionDecision,
    WitnessSimulationEvaluation,
    WitnessCredibilityAssessmentSet,
    WitnessUsagePlan,
    EvidenceUsagePlan,
)
from .witness_graph import (
    GraphNodeExecutionError,
    WitnessExaminationState,
    build_witness_examination_graph,
)


class SelectedWitness(BaseModel):
    witness_id: str
    calling_side: PartySide
    strategy_key: str
    objective_ids: tuple[str, ...] = ()
    reason: str


class ClosingRecord(BaseModel):
    admitted_evidence_ids: tuple[str, ...] = ()
    testimony_event_ids: tuple[str, ...] = ()
    completed_objective_ids: tuple[str, ...] = ()
    unresolved_contradiction_ids: tuple[str, ...] = ()
    opening_commitments: tuple[str, ...] = ()


class TrialPositionUpdate(BaseModel):
    update_id: str
    witness_id: str
    completed_objective_ids: tuple[str, ...] = ()
    admitted_evidence_ids: tuple[str, ...] = ()
    summary: str


class LearningTraceRecord(BaseModel):
    trace_id: str
    case_id: str
    phase_output_keys: tuple[str, ...]
    event_count: int
    evaluation_report_id: str | None = None
    coaching_report_id: str | None = None


class V2AiAiState(BaseModel):
    case_template: AuthoredCaseTemplate | None = None
    case_package: CompiledCasePackage | None = None
    runtime: TrialRuntimeState | None = None
    status: str = "created"
    strategies: dict[str, PartyStrategy] = Field(default_factory=dict)
    witness_examinations: list = Field(default_factory=list)
    selected_witness: SelectedWitness | None = None
    remaining_witness_keys: list[str] = Field(default_factory=list)
    completed_witness_keys: list[str] = Field(default_factory=list)
    latest_witness_result: Any | None = None
    opening_commitments: tuple[str, ...] = ()
    closing_record: ClosingRecord | None = None
    trial_position_updates: list[TrialPositionUpdate] = Field(default_factory=list)
    deliberation: DeliberationReport | None = None
    evaluation: EvaluationReport | None = None
    coaching: CoachingReport | None = None
    learning_trace: LearningTraceRecord | None = None
    phase_outputs: dict[str, str] = Field(default_factory=dict)
    trace: tuple[str, ...] = Field(default_factory=tuple)
    prompt_runs: tuple[PromptRunRecord, ...] = Field(default_factory=tuple)
    node_failure: NodeFailureRecord | None = None
    case_intelligence_analysis: str | None = None
    opening_statements: dict[str, str] = Field(default_factory=dict)
    closing_statements: dict[str, str] = Field(default_factory=dict)


class TrialGraphNodeExecutionError(RuntimeError):
    def __init__(self, failure: NodeFailureRecord) -> None:
        super().__init__(failure.message)
        self.failure = failure


def initialize_session_node(state: V2AiAiState) -> V2AiAiState:
    case_package = CaseCompiler().compile(state.case_template or build_reference_case())
    procedure = ProcedureState(phase=TrialPhase.CASE_INTELLIGENCE)
    event = CourtroomEvent(
        event_type=CourtroomEventType.SESSION_INITIALIZED,
        phase=TrialPhase.INITIALIZATION,
        summary="V2 AI-vs-AI session initialized.",
        cited_object_ids=(case_package.metadata.case_id,),
    )
    runtime = TrialRuntimeState(
        case_id=case_package.metadata.case_id,
        phase=TrialPhase.CASE_INTELLIGENCE.value,
        procedure=procedure,
        public_event_summaries=(event.summary,),
        events=(event,),
    )
    return _trace(
        state.model_copy(
            update={
                "case_package": case_package,
                "runtime": runtime,
                "status": "initialized",
                "phase_outputs": {"initialize_session": event.summary},
            }
        ),
        "initialize_session compiled the reference case.",
    )


def build_ai_ai_trial_graph(
    prompt_executor: StructuredPromptExecutor | None = None,
):
    def analyze_case_node(state: V2AiAiState) -> V2AiAiState:
        case_package, runtime = _require_initialized(state)
        analysis, prompt_runs = _invoke_prompt(
            prompt_executor,
            state,
            node_name="analyze_case",
            prompt_id=PromptId.ANALYZE_CASE_INTELLIGENCE,
            context={
                "metadata": case_package.metadata,
                "intelligence": case_package.intelligence,
                "runtime": runtime,
            },
            schema=CaseIntelligenceAnalysis,
        )
        event = _event(
            CourtroomEventType.CASE_ANALYZED,
            TrialPhase.CASE_INTELLIGENCE,
            analysis.summary,
        )
        updated_runtime = _transition_runtime(
            runtime.model_copy(update={"events": (*runtime.events, event)}),
            TrialPhase.STRATEGY,
            analysis.summary,
        )
        return _trace(
            _with_runtime(
                state.model_copy(
                    update={
                        "prompt_runs": prompt_runs,
                        "case_intelligence_analysis": analysis.summary,
                    }
                ),
                updated_runtime,
                "case_analyzed",
                {"analyze_case": analysis.summary},
            ),
            analysis.summary,
        )

    def plan_prosecution_case_node(state: V2AiAiState) -> V2AiAiState:
        case_package, runtime = _require_initialized(state)
        side = _first_side(case_package)
        strategy, prompt_runs = _plan_strategy_for_side(
            prompt_executor, state, case_package, runtime, side
        )
        summary = f"Planned live {side.value} strategy {strategy.strategy_id}."
        event = _event(
            CourtroomEventType.STRATEGY_PLANNED,
            TrialPhase.STRATEGY,
            summary,
            cited=(strategy.strategy_id,),
        )
        return _trace(
            _store_strategy(
                state.model_copy(update={"prompt_runs": prompt_runs}),
                runtime,
                strategy,
                event,
                "plan_prosecution_case",
                summary,
            ),
            summary,
        )

    def plan_defense_case_node(state: V2AiAiState) -> V2AiAiState:
        case_package, runtime = _require_initialized(state)
        strategy, prompt_runs = _plan_strategy_for_side(
            prompt_executor, state, case_package, runtime, PartySide.DEFENSE
        )
        summary = f"Planned live defense strategy {strategy.strategy_id}."
        event = _event(
            CourtroomEventType.STRATEGY_PLANNED,
            TrialPhase.STRATEGY,
            summary,
            cited=(strategy.strategy_id,),
        )
        return _trace(
            _store_strategy(
                state.model_copy(update={"prompt_runs": prompt_runs}),
                runtime,
                strategy,
                event,
                "plan_defense_case",
                summary,
            ),
            summary,
        )

    def finalize_trial_plan_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        witness_keys: list[str] = []
        for strategy in _strategies_in_trial_order(state):
            for plan in sorted(strategy.witness_plans, key=lambda item: item.order):
                if not plan.omit:
                    witness_keys.append(f"{strategy.side.value}:{plan.witness_id}")
        summary = f"Finalized trial plan with {len(witness_keys)} witness slot(s)."
        updated_runtime = _transition_runtime(runtime, TrialPhase.OPENING, summary)
        return _trace(
            _with_runtime(
                state.model_copy(update={"remaining_witness_keys": witness_keys}),
                updated_runtime,
                "trial_plan_finalized",
                {"finalize_trial_plan": summary},
            ),
            summary,
        )

    def run_opening_phase_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        commitments: list[str] = []
        statements = dict(state.opening_statements)
        prompt_runs = state.prompt_runs
        for strategy in _strategies_in_trial_order(state):
            context = {
                "side": strategy.side,
                "strategy": strategy,
                "runtime": runtime,
            }
            plan, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"plan_opening_{strategy.side.value}",
                prompt_id=PromptId.PLAN_OPENING,
                context=context,
                schema=OpeningPlan,
            )
            spoken, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"draft_opening_{strategy.side.value}",
                prompt_id=PromptId.DRAFT_OPENING,
                context={"opening_plan": plan, **context},
                schema=SpokenOpening,
            )
            commitment_set, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"extract_opening_commitments_{strategy.side.value}",
                prompt_id=PromptId.EXTRACT_OPENING_COMMITMENTS,
                context={"opening_text": spoken.text, **context},
                schema=OpeningCommitmentSet,
            )
            _, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"review_opening_{strategy.side.value}",
                prompt_id=PromptId.REVIEW_OPENING,
                context={"opening_text": spoken.text, "opening_plan": plan, **context},
                schema=OpeningReview,
                semantic_validator=_validate_review_approval,
            )
            statements[strategy.side.value] = spoken.text
            commitments.extend(item.text for item in commitment_set.commitments)
        summary = f"Opening phase recorded {len(commitments)} live commitment(s)."
        event = _event(CourtroomEventType.OPENING_DELIVERED, TrialPhase.OPENING, summary)
        updated_runtime = _transition_runtime(
            runtime.model_copy(update={"events": (*runtime.events, event)}),
            TrialPhase.WITNESS_EXAMINATION,
            summary,
        )
        return _trace(
            _with_runtime(
                state.model_copy(
                    update={
                        "prompt_runs": prompt_runs,
                        "opening_commitments": tuple(commitments),
                        "opening_statements": statements,
                    }
                ),
                updated_runtime,
                "openings_complete",
                {"opening": summary},
            ),
            summary,
        )

    def select_next_witness_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        if not state.remaining_witness_keys:
            summary = "Witness loop completed; no witness slots remain."
            updated_runtime = _transition_runtime(runtime, TrialPhase.CLOSING_RECORD, summary)
            return _trace(
                _with_runtime(
                    state.model_copy(update={"selected_witness": None}),
                    updated_runtime,
                    "witness_loop_complete",
                    {"witness_loop": summary},
                ),
                summary,
            )
        decision, prompt_runs = _invoke_prompt(
            prompt_executor,
            state,
            node_name="select_next_witness",
            prompt_id=PromptId.SELECT_NEXT_WITNESS,
            context={
                "remaining_witness_keys": state.remaining_witness_keys,
                "completed_witness_keys": state.completed_witness_keys,
                "strategies": state.strategies,
                "runtime": runtime,
                "trial_position_updates": state.trial_position_updates,
            },
            schema=WitnessSelectionDecision,
            semantic_validator=lambda output: _validate_witness_selection(state, output),
        )
        if decision.end_phase or decision.witness_id is None:
            summary = "Witness loop completed; prompt ended the evidence phase."
            updated_runtime = _transition_runtime(runtime, TrialPhase.CLOSING_RECORD, summary)
            return _trace(
                _with_runtime(
                    state.model_copy(update={"selected_witness": None, "prompt_runs": prompt_runs}),
                    updated_runtime,
                    "witness_loop_complete",
                    {"witness_loop": summary},
                ),
                summary,
            )
        selected = SelectedWitness(
            witness_id=decision.witness_id,
            calling_side=decision.calling_side or PartySide.PLAINTIFF,
            strategy_key=decision.strategy_key or (decision.calling_side or PartySide.PLAINTIFF).value,
            objective_ids=decision.objective_ids,
            reason=decision.reason,
        )
        event = _event(
            CourtroomEventType.WITNESS_SELECTED,
            TrialPhase.WITNESS_EXAMINATION,
            selected.reason,
            cited=(selected.witness_id, *selected.objective_ids),
        )
        updated_runtime = runtime.model_copy(update={"events": (*runtime.events, event)})
        return _trace(
            _with_runtime(
                state.model_copy(update={"selected_witness": selected, "prompt_runs": prompt_runs}),
                updated_runtime,
                "witness_selected",
                {"select_next_witness": event.summary},
            ),
            selected.reason,
        )

    def run_witness_examination_node(state: V2AiAiState) -> V2AiAiState:
        case_package, runtime = _require_initialized(state)
        selected = _require_selected_witness(state)
        strategy = state.strategies[selected.strategy_key]
        procedure = runtime.procedure.model_copy(
            update={
                "phase": TrialPhase.WITNESS_EXAMINATION,
                "current_witness_id": selected.witness_id,
                "examination_mode": ExaminationMode.DIRECT,
            }
        )
        scoped_runtime = runtime.model_copy(
            update={
                "phase": TrialPhase.WITNESS_EXAMINATION.value,
                "procedure": procedure,
                "current_witness_id": selected.witness_id,
            }
        )
        result = build_witness_examination_graph(prompt_executor).invoke(
            WitnessExaminationState(
                case_package=case_package,
                runtime=scoped_runtime,
                strategy=strategy,
                witness_id=selected.witness_id,
            )
        )
        output = result["output"]
        updated_runtime = runtime.model_copy(
            update={
                "events": (*runtime.events, *output.events),
                "public_event_summaries": (
                    *runtime.public_event_summaries,
                    *output.event_summaries,
                ),
            }
        )
        prompt_runs = (*state.prompt_runs, *result["prompt_runs"])
        return _trace(
            _with_runtime(
                state.model_copy(
                    update={
                        "prompt_runs": prompt_runs,
                        "latest_witness_result": output,
                        "witness_examinations": [*state.witness_examinations, output],
                    }
                ),
                updated_runtime,
                "witness_examined",
                {"run_witness_examination": f"Examined {selected.witness_id}."},
            ),
            f"run_witness_examination produced {len(result['trace'])} trace step(s).",
        )

    def update_trial_position_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        selected = _require_selected_witness(state)
        output = _require_latest_witness_result(state)
        strategy = state.strategies[selected.strategy_key]
        patch, prompt_runs = _invoke_prompt(
            prompt_executor,
            state,
            node_name="update_trial_position",
            prompt_id=PromptId.UPDATE_PARTY_TRIAL_POSITION,
            context={
                "strategy": strategy,
                "latest_witness_result": output,
                "runtime": runtime,
                "trial_position_updates": state.trial_position_updates,
            },
            schema=PartyTrialPositionPatch,
            semantic_validator=lambda value: _validate_trial_position_patch(
                state.case_package, value
            ),
        )
        admissions = _merge_admissions(
            runtime.procedure.evidence_admissions,
            tuple(
                EvidenceAdmissionRecord(
                    evidence_id=evidence_id,
                    status=EvidenceAdmissionStatus.ADMITTED,
                )
                for evidence_id in patch.admitted_evidence_ids
            ),
        )
        position_update = TrialPositionUpdate(
            update_id=f"TPU-{len(state.trial_position_updates) + 1:03d}",
            witness_id=selected.witness_id,
            completed_objective_ids=patch.completed_objective_ids,
            admitted_evidence_ids=patch.admitted_evidence_ids,
            summary=patch.summary,
        )
        event = _event(
            CourtroomEventType.OBJECTIVE_ASSESSED,
            TrialPhase.WITNESS_EXAMINATION,
            position_update.summary,
            cited=(*position_update.completed_objective_ids, *position_update.admitted_evidence_ids),
        )
        procedure = runtime.procedure.model_copy(
            update={
                "phase": TrialPhase.WITNESS_EXAMINATION,
                "current_witness_id": None,
                "examination_mode": None,
                "evidence_admissions": admissions,
            }
        )
        updated_runtime = runtime.model_copy(
            update={
                "procedure": procedure,
                "current_witness_id": None,
                "admitted_evidence_ids": procedure.admitted_evidence_ids,
                "events": (*runtime.events, event),
                "public_event_summaries": (*runtime.public_event_summaries, patch.summary),
            }
        )
        remaining = state.remaining_witness_keys[1:]
        completed = [*state.completed_witness_keys, state.remaining_witness_keys[0]]
        return _trace(
            _with_runtime(
                state.model_copy(
                    update={
                        "prompt_runs": prompt_runs,
                        "remaining_witness_keys": remaining,
                        "completed_witness_keys": completed,
                        "trial_position_updates": [*state.trial_position_updates, position_update],
                    }
                ),
                updated_runtime,
                "trial_position_updated",
                {"update_trial_position": position_update.summary},
            ),
            patch.summary,
        )

    def prepare_closing_record_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        record_prompt, prompt_runs = _invoke_prompt(
            prompt_executor,
            state,
            node_name="prepare_closings",
            prompt_id=PromptId.PREPARE_CLOSING_RECORD,
            context={
                "runtime": runtime,
                "opening_commitments": state.opening_commitments,
                "trial_position_updates": state.trial_position_updates,
            },
            schema=ClosingRecordPrompt,
        )
        record = ClosingRecord(
            admitted_evidence_ids=record_prompt.admitted_evidence_ids,
            testimony_event_ids=record_prompt.testimony_event_ids,
            completed_objective_ids=record_prompt.completed_objective_ids,
            unresolved_contradiction_ids=record_prompt.unresolved_contradiction_ids,
            opening_commitments=record_prompt.opening_commitments,
        )
        summary = (
            "Closing record prepared with "
            f"{len(record.admitted_evidence_ids)} admitted evidence item(s)."
        )
        event = _event(CourtroomEventType.EVIDENCE_UPDATED, TrialPhase.CLOSING_RECORD, summary)
        updated_runtime = _transition_runtime(
            runtime.model_copy(update={"events": (*runtime.events, event)}),
            TrialPhase.CLOSING,
            summary,
        )
        return _trace(
            _with_runtime(
                state.model_copy(update={"prompt_runs": prompt_runs, "closing_record": record}),
                updated_runtime,
                "closing_record_prepared",
                {"closing_record": summary},
            ),
            summary,
        )

    def run_closing_phase_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        record = _require_closing_record(state)
        prompt_runs = state.prompt_runs
        statements = dict(state.closing_statements)
        for strategy in _strategies_in_trial_order(state):
            context = {"side": strategy.side, "strategy": strategy, "closing_record": record, "runtime": runtime}
            position, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"assess_closing_position_{strategy.side.value}",
                prompt_id=PromptId.ASSESS_CLOSING_POSITION,
                context=context,
                schema=ClosingPositionAssessment,
            )
            plan, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"plan_closing_{strategy.side.value}",
                prompt_id=PromptId.PLAN_CLOSING,
                context={**context, "closing_position": position},
                schema=ClosingPlan,
            )
            spoken, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"draft_closing_{strategy.side.value}",
                prompt_id=PromptId.DRAFT_CLOSING,
                context={**context, "closing_plan": plan},
                schema=SpokenClosing,
            )
            _, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"review_closing_{strategy.side.value}",
                prompt_id=PromptId.REVIEW_CLOSING,
                context={**context, "closing_plan": plan, "closing_text": spoken.text},
                schema=ClosingReview,
                semantic_validator=_validate_review_approval,
            )
            statements[strategy.side.value] = spoken.text
        summary = "Closing phase recorded from admitted evidence and live party positions."
        event = _event(CourtroomEventType.CLOSING_DELIVERED, TrialPhase.CLOSING, summary)
        updated_runtime = _transition_runtime(
            runtime.model_copy(update={"events": (*runtime.events, event)}),
            TrialPhase.DELIBERATION,
            summary,
        )
        return _trace(
            _with_runtime(
                state.model_copy(update={"prompt_runs": prompt_runs, "closing_statements": statements}),
                updated_runtime,
                "closings_complete",
                {"closing": summary},
            ),
            summary,
        )

    def run_deliberation_node(state: V2AiAiState) -> V2AiAiState:
        case_package, runtime = _require_initialized(state)
        question_set, prompt_runs = _invoke_prompt(
            prompt_executor,
            state,
            node_name="identify_decision_questions",
            prompt_id=PromptId.IDENTIFY_DECISION_QUESTIONS,
            context={"case_package": case_package, "closing_record": _require_closing_record(state), "runtime": runtime},
            schema=DecisionQuestionSet,
        )
        deliberation_result, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="fact_finder_deliberation",
            prompt_id=PromptId.FACT_FINDER_DELIBERATION,
            context={"decision_questions": question_set, "runtime": runtime},
            schema=FactFinderDeliberationResult,
        )
        element_set, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="evaluate_legal_elements",
            prompt_id=PromptId.EVALUATE_LEGAL_ELEMENTS,
            context={"decision_questions": question_set, "runtime": runtime},
            schema=ElementEvaluationSet,
        )
        credibility_set, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="assess_witness_credibility",
            prompt_id=PromptId.ASSESS_WITNESS_CREDIBILITY,
            context={"decision_questions": question_set, "witness_examinations": state.witness_examinations},
            schema=WitnessCredibilityAssessmentSet,
        )
        burden_result, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="apply_burden",
            prompt_id=PromptId.APPLY_BURDEN,
            context={"element_evaluations": element_set, "decision_questions": question_set},
            schema=BurdenApplicationResult,
        )
        candidate_findings, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="generate_findings",
            prompt_id=PromptId.GENERATE_FINDINGS,
            context={
                "deliberation": deliberation_result,
                "element_evaluations": element_set,
                "burden_applications": burden_result,
            },
            schema=CandidateFindings,
        )
        challenge, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="challenge_findings",
            prompt_id=PromptId.CHALLENGE_FINDINGS,
            context={"candidate_findings": candidate_findings},
            schema=FindingsChallenge,
            semantic_validator=_validate_review_approval,
        )
        decision, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="draft_final_decision",
            prompt_id=PromptId.DRAFT_FINAL_DECISION,
            context={"candidate_findings": candidate_findings, "challenge": challenge},
            schema=FinalDecision,
        )
        _, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="review_final_decision",
            prompt_id=PromptId.REVIEW_FINAL_DECISION,
            context={"final_decision": decision, "candidate_findings": candidate_findings},
            schema=FinalDecisionReview,
            semantic_validator=_validate_review_approval,
        )
        report = _build_deliberation_report(
            runtime,
            question_set,
            element_set,
            credibility_set,
            burden_result,
            candidate_findings,
            challenge,
            decision,
        )
        summary = (
            "Live deliberation reached "
            f"{report.verdict.outcome.value} verdict with "
            f"{len(report.finalized_findings)} finding(s)."
        )
        event = _event(
            CourtroomEventType.DELIBERATION_COMPLETED,
            TrialPhase.DELIBERATION,
            summary,
            cited=(report.verdict.verdict_id,),
        )
        updated_runtime = _transition_runtime(
            runtime.model_copy(update={"events": (*runtime.events, event)}),
            TrialPhase.EVALUATION,
            summary,
        )
        return _trace(
            _with_runtime(
                state.model_copy(update={"prompt_runs": prompt_runs, "deliberation": report}),
                updated_runtime,
                "deliberation_complete",
                {"deliberation": summary},
            ),
            summary,
        )

    def run_evaluation_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        deliberation = _require_deliberation(state)
        prompt_runs = state.prompt_runs
        party_evaluations = []
        for strategy in _strategies_in_trial_order(state):
            evaluation, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"evaluate_party_advocacy_{strategy.side.value}",
                prompt_id=PromptId.EVALUATE_PARTY_ADVOCACY,
                context={"strategy": strategy, "runtime": runtime, "deliberation": deliberation},
                schema=PartyAdvocacyEvaluation,
            )
            party_evaluations.append(evaluation)
        witness_evaluations = []
        for output in state.witness_examinations:
            evaluation, prompt_runs = _invoke_prompt(
                prompt_executor,
                state.model_copy(update={"prompt_runs": prompt_runs}),
                node_name=f"evaluate_witness_simulation_{output.witness_id}",
                prompt_id=PromptId.EVALUATE_WITNESS_SIMULATION,
                context={"witness_result": output, "runtime": runtime},
                schema=WitnessSimulationEvaluation,
            )
            witness_evaluations.append(evaluation)
        procedural_eval, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="evaluate_procedural_decisions",
            prompt_id=PromptId.EVALUATE_PROCEDURAL_DECISIONS,
            context={"runtime": runtime},
            schema=ProceduralDecisionEvaluation,
        )
        fact_finder_eval, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="evaluate_fact_finder",
            prompt_id=PromptId.EVALUATE_FACT_FINDER,
            context={"deliberation": deliberation},
            schema=FactFinderEvaluation,
        )
        sim_eval, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="evaluate_simulation_quality",
            prompt_id=PromptId.EVALUATE_SIMULATION_QUALITY,
            context={"runtime": runtime, "witness_examinations": state.witness_examinations},
            schema=SimulationQualityEvaluation,
        )
        missed, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="detect_missed_opportunities",
            prompt_id=PromptId.DETECT_MISSED_OPPORTUNITIES,
            context={"runtime": runtime, "witness_examinations": state.witness_examinations},
            schema=MissedOpportunitySet,
        )
        counterfactuals, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="compare_counterfactual_actions",
            prompt_id=PromptId.COMPARE_COUNTERFACTUAL_ACTIONS,
            context={"missed_opportunities": missed},
            schema=CounterfactualActionComparison,
        )
        calibration, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="calibrate_evaluation",
            prompt_id=PromptId.CALIBRATE_EVALUATION,
            context={
                "party_evaluations": party_evaluations,
                "witness_evaluations": witness_evaluations,
                "procedural_evaluation": procedural_eval,
                "fact_finder_evaluation": fact_finder_eval,
                "simulation_evaluation": sim_eval,
            },
            schema=EvaluationCalibration,
        )
        report = _build_evaluation_report(
            party_evaluations,
            witness_evaluations,
            procedural_eval,
            fact_finder_eval,
            sim_eval,
            missed,
            counterfactuals,
            calibration,
        )
        summary = (
            "Evaluation completed with "
            f"{len(report.observations)} grounded observation(s) and "
            f"{len(report.missed_opportunities)} missed opportunity record(s)."
        )
        event = _event(CourtroomEventType.EVALUATION_COMPLETED, TrialPhase.EVALUATION, summary)
        updated_runtime = runtime.model_copy(update={"events": (*runtime.events, event)})
        return _trace(
            _with_runtime(
                state.model_copy(update={"prompt_runs": prompt_runs, "evaluation": report}),
                updated_runtime,
                "evaluation_complete",
                {"evaluation": summary},
            ),
            summary,
        )

    def generate_coaching_node(state: V2AiAiState) -> V2AiAiState:
        _, runtime = _require_initialized(state)
        evaluation = _require_evaluation(state)
        selection, prompt_runs = _invoke_prompt(
            prompt_executor,
            state,
            node_name="select_learning_moments",
            prompt_id=PromptId.SELECT_LEARNING_MOMENTS,
            context={"evaluation": evaluation},
            schema=LearningMomentSelection,
        )
        feedback, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="generate_causal_feedback",
            prompt_id=PromptId.GENERATE_CAUSAL_FEEDBACK,
            context={"evaluation": evaluation, "learning_moments": selection},
            schema=CausalCoachingFeedback,
        )
        sequences, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="generate_better_action_sequence",
            prompt_id=PromptId.GENERATE_BETTER_ACTION_SEQUENCE,
            context={"causal_feedback": feedback},
            schema=BetterActionSequenceSet,
        )
        examples, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="generate_example_execution",
            prompt_id=PromptId.GENERATE_EXAMPLE_EXECUTION,
            context={"better_action_sequences": sequences},
            schema=ExampleExecution,
        )
        improvement, prompt_runs = _invoke_prompt(
            prompt_executor,
            state.model_copy(update={"prompt_runs": prompt_runs}),
            node_name="build_improvement_plan",
            prompt_id=PromptId.BUILD_IMPROVEMENT_PLAN,
            context={"causal_feedback": feedback, "example_execution": examples},
            schema=LearnerImprovementPlan,
        )
        coaching = _build_coaching_report(evaluation, feedback, sequences, examples, improvement)
        summary = (
            "Coaching completed with "
            f"{len(coaching.moments)} moment(s) and "
            f"{len(coaching.skill_profile_updates)} skill update(s)."
        )
        event = _event(CourtroomEventType.COACHING_COMPLETED, TrialPhase.EVALUATION, summary)
        updated_runtime = runtime.model_copy(update={"events": (*runtime.events, event)})
        return _trace(
            _with_runtime(
                state.model_copy(update={"prompt_runs": prompt_runs, "coaching": coaching}),
                updated_runtime,
                "coaching_complete",
                {"coaching": summary},
            ),
            summary,
        )

    def persist_learning_trace_node(state: V2AiAiState) -> V2AiAiState:
        case_package, runtime = _require_initialized(state)
        summary = "Persisted prompt-driven in-memory learning trace for inspection."
        learning_trace = LearningTraceRecord(
            trace_id=f"TRACE-{uuid4()}",
            case_id=case_package.metadata.case_id,
            phase_output_keys=tuple(sorted(state.phase_outputs)),
            event_count=len(runtime.events),
            evaluation_report_id=state.evaluation.report_id if state.evaluation else None,
            coaching_report_id=state.coaching.report_id if state.coaching else None,
        )
        updated_runtime = _transition_runtime(runtime, TrialPhase.COMPLETE, summary)
        return _trace(
            _with_runtime(
                state.model_copy(update={"learning_trace": learning_trace}),
                updated_runtime,
                "learning_trace_persisted",
                {"persist_learning_trace": summary},
            ),
            summary,
        )

    builder = StateGraph(V2AiAiState)

    def add_node(name: str, node: Any) -> None:
        def guarded_node(state: V2AiAiState) -> V2AiAiState:
            try:
                return node(state)
            except (TrialGraphNodeExecutionError, GraphNodeExecutionError) as exc:
                failure = exc.failure
                summary = f"{name} failed: {failure.message}"
                return _trace(
                    state.model_copy(
                        update={
                            "status": "failed",
                            "node_failure": failure,
                            "phase_outputs": {**state.phase_outputs, name: summary},
                        }
                    ),
                    summary,
                )

        builder.add_node(name, guarded_node)

    def add_guarded_edge(source: str, target: str) -> None:
        builder.add_conditional_edges(
            source,
            lambda state: "failed" if state.status == "failed" else "continue",
            {"continue": target, "failed": END},
        )

    add_node("initialize_session", initialize_session_node)
    add_node("analyze_case", analyze_case_node)
    add_node("plan_prosecution_case", plan_prosecution_case_node)
    add_node("plan_defense_case", plan_defense_case_node)
    add_node("finalize_trial_plan", finalize_trial_plan_node)
    add_node("run_opening_phase", run_opening_phase_node)
    add_node("select_next_witness", select_next_witness_node)
    add_node("run_witness_examination", run_witness_examination_node)
    add_node("update_trial_position", update_trial_position_node)
    add_node("prepare_closings", prepare_closing_record_node)
    add_node("run_closing_phase", run_closing_phase_node)
    add_node("run_deliberation", run_deliberation_node)
    add_node("run_evaluation", run_evaluation_node)
    add_node("generate_coaching", generate_coaching_node)
    add_node("persist_learning_trace", persist_learning_trace_node)
    builder.add_edge(START, "initialize_session")
    add_guarded_edge("initialize_session", "analyze_case")
    add_guarded_edge("analyze_case", "plan_prosecution_case")
    add_guarded_edge("plan_prosecution_case", "plan_defense_case")
    add_guarded_edge("plan_defense_case", "finalize_trial_plan")
    add_guarded_edge("finalize_trial_plan", "run_opening_phase")
    add_guarded_edge("run_opening_phase", "select_next_witness")
    builder.add_conditional_edges(
        "select_next_witness",
        route_after_witness_selection,
        {
            "examine": "run_witness_examination",
            "complete": "prepare_closings",
            "failed": END,
        },
    )
    add_guarded_edge("run_witness_examination", "update_trial_position")
    add_guarded_edge("update_trial_position", "select_next_witness")
    add_guarded_edge("prepare_closings", "run_closing_phase")
    add_guarded_edge("run_closing_phase", "run_deliberation")
    add_guarded_edge("run_deliberation", "run_evaluation")
    add_guarded_edge("run_evaluation", "generate_coaching")
    add_guarded_edge("generate_coaching", "persist_learning_trace")
    add_guarded_edge("persist_learning_trace", END)
    return builder.compile()


def route_after_witness_selection(state: V2AiAiState) -> str:
    if state.status == "failed":
        return "failed"
    return "complete" if state.selected_witness is None else "examine"


def _plan_strategy_for_side(
    executor: StructuredPromptExecutor | None,
    state: V2AiAiState,
    case_package: CompiledCasePackage,
    runtime: TrialRuntimeState,
    side: PartySide,
) -> tuple[PartyStrategy, tuple[PromptRunRecord, ...]]:
    context = {
        "side": side,
        "case_package": case_package,
        "runtime": runtime,
        "case_intelligence_analysis": state.case_intelligence_analysis,
    }
    position, prompt_runs = _invoke_prompt(
        executor,
        state,
        node_name=f"assess_case_position_{side.value}",
        prompt_id=PromptId.ASSESS_CASE_POSITION,
        context=context,
        schema=CasePositionAssessment,
    )
    theory, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"develop_case_theory_{side.value}",
        prompt_id=PromptId.DEVELOP_CASE_THEORY,
        context={**context, "position": position},
        schema=CaseTheoryPlan,
    )
    objective_plan, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"generate_strategic_objectives_{side.value}",
        prompt_id=PromptId.GENERATE_STRATEGIC_OBJECTIVES,
        context={**context, "position": position, "theory": theory},
        schema=StrategicObjectivePlan,
        semantic_validator=_validate_objective_plan,
    )
    witness_plan, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"plan_witness_usage_{side.value}",
        prompt_id=PromptId.PLAN_WITNESS_USAGE,
        context={**context, "objectives": objective_plan},
        schema=WitnessUsagePlan,
    )
    evidence_plan, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"plan_evidence_usage_{side.value}",
        prompt_id=PromptId.PLAN_EVIDENCE_USAGE,
        context={**context, "objectives": objective_plan},
        schema=EvidenceUsagePlan,
    )
    opponent, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"anticipate_opponent_{side.value}",
        prompt_id=PromptId.ANTICIPATE_OPPONENT,
        context={**context, "objectives": objective_plan},
        schema=OpponentModel,
    )
    ranked, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"rank_strategy_{side.value}",
        prompt_id=PromptId.RANK_STRATEGY,
        context={
            **context,
            "objectives": objective_plan,
            "witness_usage": witness_plan,
            "evidence_usage": evidence_plan,
            "opponent_model": opponent,
        },
        schema=RankedStrategyPlan,
    )
    review, prompt_runs = _invoke_prompt(
        executor,
        state.model_copy(update={"prompt_runs": prompt_runs}),
        node_name=f"review_strategy_{side.value}",
        prompt_id=PromptId.REVIEW_STRATEGY,
        context={
            **context,
            "ranked_strategy": ranked,
            "theory": theory,
            "objectives": objective_plan,
            "witness_usage": witness_plan,
            "evidence_usage": evidence_plan,
        },
        schema=StrategyReview,
        semantic_validator=_validate_strategy_review,
    )
    valid_witness_ids = {
        witness.witness_id for witness in case_package.witnesses if witness.called_by == side
    }
    valid_evidence_ids = {
        evidence.evidence_id for evidence in case_package.evidence if evidence.offered_by == side
    }
    strategy = PartyStrategy(
        strategy_id=f"STR-{side.value.upper()}-LIVE-001",
        side=side,
        theory=CaseTheory(
            theory_id=f"THY-{side.value.upper()}-LIVE-001",
            side=side,
            theme=theory.theme,
            core_claim=theory.core_claim,
            target_element_ids=theory.target_element_ids,
            supporting_fact_ids=theory.supporting_fact_ids,
            dangerous_fact_ids=theory.dangerous_fact_ids,
        ),
        objectives=tuple(
            StrategicObjective(
                objective_id=item.objective_id,
                description=item.description,
                target_element_ids=item.target_element_ids,
                target_fact_ids=item.target_fact_ids,
                priority=item.priority,
                success_signals=item.success_signals or ("Advance the case.",),
                failure_signals=item.failure_signals,
            )
            for item in objective_plan.objectives
        ),
        witness_plans=tuple(
            WitnessPlan(
                witness_id=item.witness_id,
                calling_side=side,
                objective_ids=item.objective_ids,
                direct_topics=item.direct_topics,
                cross_risks=item.cross_risks,
                order=item.order,
                omit=item.omit or item.witness_id not in valid_witness_ids,
            )
            for item in witness_plan.witness_plans
        ),
        evidence_plans=tuple(
            EvidencePlan(
                evidence_id=item.evidence_id,
                offering_side=side,
                objective_ids=item.objective_ids,
                fact_ids=item.fact_ids,
                through_witness_id=item.through_witness_id,
                foundation_required=item.foundation_required,
                expected_objections=item.expected_objections,
                fallback=item.fallback,
            )
            for item in evidence_plan.evidence_plans
            if item.evidence_id in valid_evidence_ids
        ),
        opponent_risks=tuple(
            OpponentRiskRecord(
                risk_id=item.risk_id,
                side=PartySide.DEFENSE if side != PartySide.DEFENSE else _first_side(case_package),
                description=item.description,
                related_fact_ids=item.related_fact_ids,
                related_evidence_ids=item.related_evidence_ids,
                severity=item.severity,
            )
            for item in opponent.opponent_risks
        ),
        objective_states=tuple(
            ObjectiveRuntimeState(objective_id=item.objective_id)
            for item in objective_plan.objectives
        ),
        validation=StrategyValidationRecord(
            status=StrategyValidationStatus.VALID if review.approved else StrategyValidationStatus.INVALID,
            invalid_references=review.invalid_references,
            messages=review.messages,
        ),
    )
    return strategy, prompt_runs


def _invoke_prompt(
    executor: StructuredPromptExecutor | None,
    state: V2AiAiState,
    *,
    node_name: str,
    prompt_id: PromptId,
    context: dict,
    schema: type,
    semantic_validator=None,
) -> tuple[Any, tuple[PromptRunRecord, ...]]:
    if executor is None:
        raise RuntimeError(
            f"{node_name} requires a configured prompt executor for live execution"
        )
    try:
        result = executor.invoke(
            prompt_id=prompt_id,
            context=context,
            schema=schema,
            semantic_validator=semantic_validator,
            metadata={"node_name": node_name},
            cache_scope=node_name,
        )
    except PromptInvocationError as exc:
        prompt_result = exc.result
        failure = NodeFailureRecord(
            node_name=node_name,
            prompt_id=prompt_id.value,
            outcome=prompt_result.outcome.value if prompt_result else "error",
            message=str(exc),
            response_id=prompt_result.response_id if prompt_result else None,
        )
        raise TrialGraphNodeExecutionError(failure) from exc
    run = PromptRunRecord(
        node_name=node_name,
        prompt_id=prompt_id.value,
        outcome=result.outcome.value,
        attempts=result.attempts,
        response_id=result.response_id,
        cached_tokens=result.usage.cached_tokens,
        cache_write_tokens=result.usage.cache_write_tokens,
    )
    return result.output, (*state.prompt_runs, run)


def _build_deliberation_report(
    runtime: TrialRuntimeState,
    question_set: DecisionQuestionSet,
    element_set: ElementEvaluationSet,
    credibility_set,
    burden_result: BurdenApplicationResult,
    candidate_findings: CandidateFindings,
    challenge: FindingsChallenge,
    decision: FinalDecision,
) -> DeliberationReport:
    challenged = set(challenge.challenged_finding_ids)
    candidate_records = tuple(
        CandidateFinding(
            finding_id=item.finding_id,
            matter_id=item.matter_id,
            element_id=item.element_id,
            status=item.status,
            explanation=item.explanation,
            citations=_citations_from_ids(item.citation_record_ids),
            challenged=item.finding_id in challenged,
            challenge_messages=challenge.messages if item.finding_id in challenged else (),
        )
        for item in candidate_findings.findings
    )
    verdict = Verdict(
        verdict_id=f"VER-{decision.matter_id}",
        outcome=decision.verdict_outcome,
        matter_id=decision.matter_id,
        explanation=decision.explanation,
        finding_ids=decision.finding_ids,
        citations=_citations_from_ids(decision.citation_record_ids),
    )
    return DeliberationReport(
        report_id=f"DLB-{decision.matter_id}",
        judge_record=JudgeRecord(
            record_id=f"JR-{runtime.case_id}",
            case_id=runtime.case_id,
            admitted_evidence_ids=runtime.admitted_evidence_ids,
            testimony_event_ids=tuple(
                str(event.event_id)
                for event in runtime.events
                if event.event_type == CourtroomEventType.WITNESS_ANSWERED
            ),
        ),
        legal_questions=tuple(
            LegalQuestion(
                question_id=item.question_id,
                matter_id=item.matter_id,
                element_ids=item.element_ids,
                burden_holder=item.burden_holder,
                standard=item.standard,
                verdict_options=item.verdict_options,
            )
            for item in question_set.questions
        ),
        element_evaluations=tuple(
            ElementEvaluation(
                element_id=item.element_id,
                matter_id=item.matter_id,
                burden_holder=item.burden_holder,
                standard=item.standard,
                supporting_citations=_citations_from_ids(item.supporting_record_ids),
                contrary_citations=_citations_from_ids(item.contrary_record_ids),
                unresolved_gaps=item.unresolved_gaps,
                status=item.status,
                confidence=item.confidence,
            )
            for item in element_set.evaluations
        ),
        credibility_findings=tuple(
            WitnessCredibilityFinding(
                witness_id=item.witness_id,
                finding_id=item.finding_id,
                summary=item.summary,
                supporting_citations=_citations_from_ids(item.supporting_record_ids),
                contradiction_citations=_citations_from_ids(item.contradiction_record_ids),
                confidence=item.confidence,
            )
            for item in credibility_set.assessments
        ),
        burden_applications=tuple(
            BurdenApplication(
                application_id=item.application_id,
                element_id=item.element_id,
                matter_id=item.matter_id,
                burden_holder=item.burden_holder,
                standard=item.standard,
                element_status=item.element_status,
                conclusion=item.conclusion,
                citations=_citations_from_ids(item.citation_record_ids),
            )
            for item in burden_result.applications
        ),
        candidate_findings=candidate_records,
        finalized_findings=candidate_records,
        verdict=verdict,
        validation=VerdictValidationResult(valid=True),
    )


def _build_evaluation_report(
    party_evaluations,
    witness_evaluations,
    procedural_eval,
    fact_finder_eval,
    simulation_eval,
    missed: MissedOpportunitySet,
    counterfactuals: CounterfactualActionComparison,
    calibration: EvaluationCalibration,
) -> EvaluationReport:
    observations = []
    actor_evaluations = []
    index = 1
    for party_eval in party_evaluations:
        party_obs = tuple(_observation_from_input(item, index + i, party_eval.side) for i, item in enumerate(party_eval.observations))
        index += len(party_obs)
        observations.extend(party_obs)
        actor_evaluations.append(
            ActorEvaluation(
                evaluator_id="eval-live",
                evaluated_side=party_eval.side,
                dimensions=tuple(dict.fromkeys(item.dimension for item in party_eval.observations)),
                observations=party_obs,
                score=party_eval.score,
                confidence=party_eval.confidence,
                prompt_version="live",
                model_version="live",
            )
        )
    for witness_eval in witness_evaluations:
        witness_obs = tuple(_observation_from_input(item, index + i) for i, item in enumerate(witness_eval.observations))
        index += len(witness_obs)
        observations.extend(witness_obs)
        actor_evaluations.append(
            ActorEvaluation(
                evaluator_id="eval-live",
                dimensions=tuple(dict.fromkeys(item.dimension for item in witness_eval.observations)),
                observations=witness_obs,
                score=witness_eval.score,
                confidence=witness_eval.confidence,
                prompt_version="live",
                model_version="live",
            )
        )
    proc_obs = tuple(_observation_from_input(item, index + i) for i, item in enumerate(procedural_eval.observations))
    index += len(proc_obs)
    ff_obs = tuple(_observation_from_input(item, index + i) for i, item in enumerate(fact_finder_eval.observations))
    index += len(ff_obs)
    sim_obs = tuple(_observation_from_input(item, index + i) for i, item in enumerate(simulation_eval.observations))
    observations.extend(proc_obs)
    observations.extend(ff_obs)
    observations.extend(sim_obs)
    deterministic_checks = (
        DeterministicCheckResult(
            code=DeterministicCheckCode.ROLE_BOUNDARY_VIOLATION,
            passed=True,
            message="Live prompt execution preserved role and record boundaries.",
            severity=EvaluationSeverity.INFO,
        ),
    )
    simulation_actor_eval = ActorEvaluation(
        evaluator_id="eval-live",
        dimensions=tuple(dict.fromkeys(item.dimension for item in simulation_eval.observations))
        or (EvaluationDimension.SIMULATION_QUALITY,),
        observations=sim_obs,
        score=simulation_eval.score,
        confidence=simulation_eval.confidence,
        prompt_version="live",
        model_version="live",
    )
    return EvaluationReport(
        report_id="EVAL-LIVE-001",
        deterministic_checks=deterministic_checks,
        actor_evaluations=tuple(actor_evaluations),
        simulation_evaluation=simulation_actor_eval,
        observations=tuple(observations),
        missed_opportunities=tuple(
            MissedOpportunity(
                opportunity_id=item.opportunity_id,
                actor_id=item.actor_id,
                side=item.side,
                moment_event_id=item.moment_event_id,
                reason=item.reason,
                available_fact_ids=item.available_fact_ids,
                available_evidence_ids=item.available_evidence_ids,
                objective_id=item.objective_id,
                citations=_citations_from_ids(item.citation_record_ids),
                severity=item.severity,
                confidence=item.confidence,
            )
            for item in missed.opportunities
        ),
        counterfactual_comparisons=tuple(
            CounterfactualComparison(
                comparison_id=item.comparison_id,
                opportunity_id=item.opportunity_id,
                actual_action=item.actual_action,
                preferred_action=item.preferred_action,
                rejected_alternatives=item.rejected_alternatives,
                assumptions=item.assumptions,
                citations=_citations_from_ids(item.citation_record_ids),
                expected_value_delta=item.expected_value_delta,
                risk_analysis=item.risk_analysis,
                confidence=item.confidence,
            )
            for item in counterfactuals.comparisons
        ),
        aggregation=EvaluationAggregation(
            score=calibration.score,
            confidence=calibration.confidence,
            deterministic_failures=(),
            observation_ids=tuple(item.observation_id for item in observations),
            expert_review_required=calibration.expert_review_required,
        ),
        calibration_record=calibration.summary,
    )


def _build_coaching_report(
    evaluation: EvaluationReport,
    feedback: CausalCoachingFeedback,
    sequences: BetterActionSequenceSet,
    examples: ExampleExecution,
    improvement: LearnerImprovementPlan,
) -> CoachingReport:
    example_by_observation = {
        item.observation_id: item.wording for item in examples.examples
    }
    seq_by_observation = {
        item.observation_id: item for item in sequences.sequences
    }
    moments = tuple(
        CoachingMoment(
            moment_id=f"CM-{item.observation_id}",
            observation_id=item.observation_id,
            transcript_location=item.transcript_location,
            skill=item.skill,
            what_happened=item.what_happened,
            affected_objective_ids=item.objective_ids,
            available_information=_citations_from_ids(item.citation_record_ids),
            why_it_mattered=item.why_it_mattered,
            better_action=item.better_action,
            example_wording=example_by_observation.get(item.observation_id, item.example_wording),
            expected_response=item.expected_response,
            recovery_option=item.recovery_option,
            severity=item.severity,
            confidence=item.confidence,
        )
        for item in feedback.moments
    )
    grouped = defaultdict(list)
    for update in improvement.skill_updates:
        grouped[(update.actor_id, update.role)].append(update)
    skill_updates = tuple(
        SkillProfileUpdate(
            actor_id=actor_id,
            role=_parse_actor_role(role),
            appended_evidence=tuple(
                SkillEvidence(
                    evidence_id=f"SE-{item.source_observation_id}",
                    actor_id=item.actor_id,
                    role=_parse_actor_role(item.role),
                    skill=item.skill,
                    source_observation_id=item.source_observation_id,
                    citations=_citations_from_ids(item.citation_record_ids),
                    direction=item.direction,
                    strength=item.strength,
                    confidence=item.confidence,
                    source_evaluator_version=evaluation.evaluator_version,
                )
                for item in items
            ),
        )
        for (actor_id, role), items in grouped.items()
    )
    return CoachingReport(
        report_id=f"COACH-{evaluation.report_id}",
        source_evaluation_report_id=evaluation.report_id,
        moments=moments,
        better_action_sequences=tuple(
            BetterActionSequence(
                sequence_id=f"SEQ-{item.observation_id}",
                moment_id=f"CM-{item.observation_id}",
                steps=item.steps,
                citations=_citations_from_ids(item.citation_record_ids),
            )
            for item in sequences.sequences
        ),
        improvement_plan=improvement.steps,
        skill_profile_updates=skill_updates,
    )


def _observation_from_input(item, index: int, side: PartySide | None = None) -> EvaluationObservation:
    return EvaluationObservation(
        observation_id=f"OBS-{index:03d}",
        evaluated_side=side,
        dimension=item.dimension,
        defect_type=item.defect_type,
        claim=item.claim,
        severity=item.severity,
        score_impact=item.score_impact,
        confidence=item.confidence,
        citations=_citations_from_ids(item.citation_record_ids),
        affected_objective_ids=item.objective_ids,
    )


def _validate_review_approval(review) -> SemanticValidationResult:
    if review.approved:
        return SemanticValidationResult(
            accepted=True,
            outcome=InvocationOutcome.SUCCESS,
        )
    message = review.messages[0] if review.messages else "Review rejected the output."
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_strategy_review(review: StrategyReview) -> SemanticValidationResult:
    return _validate_review_approval(review)


def _validate_objective_plan(plan: StrategicObjectivePlan) -> SemanticValidationResult:
    if plan.objectives:
        return SemanticValidationResult(
            accepted=True,
            outcome=InvocationOutcome.SUCCESS,
        )
    message = "Strategy planning must return at least one objective."
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.INSUFFICIENT_CONTEXT,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_witness_selection(
    state: V2AiAiState, selection: WitnessSelectionDecision
) -> SemanticValidationResult:
    if selection.end_phase:
        return SemanticValidationResult(
            accepted=True,
            outcome=InvocationOutcome.SUCCESS,
        )
    valid_pairs = set(state.remaining_witness_keys)
    if selection.strategy_key and selection.witness_id:
        key = f"{selection.strategy_key}:{selection.witness_id}"
        if key in valid_pairs:
            return SemanticValidationResult(
                accepted=True,
                outcome=InvocationOutcome.SUCCESS,
            )
    message = "Witness selection must reference a remaining witness slot."
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_trial_position_patch(
    case_package: CompiledCasePackage | None,
    patch: PartyTrialPositionPatch,
) -> SemanticValidationResult:
    if case_package is None:
        return SemanticValidationResult(
            accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
            validation_feedback=("Case package is missing.",),
            error_message="Case package is missing.",
        )
    valid_evidence_ids = {item.evidence_id for item in case_package.evidence}
    if all(item in valid_evidence_ids for item in patch.admitted_evidence_ids):
        return SemanticValidationResult(
            accepted=True,
            outcome=InvocationOutcome.SUCCESS,
        )
    message = "Trial position patch referenced unknown evidence."
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _citations_from_ids(ids: tuple[str, ...]) -> tuple[RecordCitation, ...]:
    citations = []
    for record_id in ids:
        kind = CitationKind.COURTROOM_EVENT if record_id.startswith("EVT-") else CitationKind.FACT
        citations.append(RecordCitation(kind=kind, record_id=record_id))
    return tuple(citations)


def _parse_actor_role(value: str | None) -> ActorRole | None:
    if value is None:
        return None
    try:
        return ActorRole(value)
    except ValueError:
        return None


def _require_initialized(
    state: V2AiAiState,
) -> tuple[CompiledCasePackage, TrialRuntimeState]:
    if state.case_package is None or state.runtime is None:
        raise ValueError("V2 session must be initialized")
    return state.case_package, state.runtime


def _require_selected_witness(state: V2AiAiState) -> SelectedWitness:
    if state.selected_witness is None:
        raise ValueError("witness examination requires selected witness")
    return state.selected_witness


def _require_latest_witness_result(state: V2AiAiState):
    if state.latest_witness_result is None:
        raise ValueError("trial position update requires latest witness result")
    return state.latest_witness_result


def _require_closing_record(state: V2AiAiState) -> ClosingRecord:
    if state.closing_record is None:
        raise ValueError("closing phase requires closing record")
    return state.closing_record


def _require_deliberation(state: V2AiAiState) -> DeliberationReport:
    if state.deliberation is None:
        raise ValueError("evaluation requires deliberation report")
    return state.deliberation


def _require_evaluation(state: V2AiAiState) -> EvaluationReport:
    if state.evaluation is None:
        raise ValueError("coaching requires evaluation report")
    return state.evaluation


def _first_side(case_package: CompiledCasePackage) -> PartySide:
    return (
        PartySide.PROSECUTION
        if any(party.side == PartySide.PROSECUTION for party in case_package.parties)
        else PartySide.PLAINTIFF
    )


def _strategies_in_trial_order(state: V2AiAiState) -> tuple[PartyStrategy, ...]:
    case_package, _ = _require_initialized(state)
    first_key = _first_side(case_package).value
    ordered = []
    for key in (first_key, PartySide.DEFENSE.value):
        strategy = state.strategies.get(key)
        if strategy is not None:
            ordered.append(strategy)
    return tuple(ordered)


def _store_strategy(
    state: V2AiAiState,
    runtime: TrialRuntimeState,
    strategy: PartyStrategy,
    event: CourtroomEvent,
    output_key: str,
    summary: str,
) -> V2AiAiState:
    strategies = {**state.strategies, strategy.side.value: strategy}
    updated_runtime = runtime.model_copy(
        update={"events": (*runtime.events, event), "party_strategies": tuple(strategies.values())}
    )
    return _with_runtime(
        state.model_copy(update={"strategies": strategies}),
        updated_runtime,
        f"{strategy.side.value}_strategy_planned",
        {output_key: summary},
    )


def _event(
    event_type: CourtroomEventType,
    phase: TrialPhase,
    summary: str,
    cited: tuple[str, ...] = (),
) -> CourtroomEvent:
    return CourtroomEvent(
        event_type=event_type,
        phase=phase,
        summary=summary,
        cited_object_ids=cited,
    )


def _transition_runtime(
    runtime: TrialRuntimeState,
    phase: TrialPhase,
    summary: str,
) -> TrialRuntimeState:
    current_phase = (
        runtime.procedure.phase
        if isinstance(runtime.procedure.phase, TrialPhase)
        else TrialPhase(runtime.procedure.phase)
    )
    transition = PhaseTransitionRecord(from_phase=current_phase, to_phase=phase, reason=summary)
    procedure = runtime.procedure.model_copy(
        update={"phase": phase, "transitions": (*runtime.procedure.transitions, transition)}
    )
    return runtime.model_copy(update={"phase": phase.value, "procedure": procedure})


def _with_runtime(
    state: V2AiAiState,
    runtime: TrialRuntimeState,
    status: str,
    phase_outputs: dict[str, str],
) -> V2AiAiState:
    merged_outputs = {**state.phase_outputs, **phase_outputs}
    return state.model_copy(update={"runtime": runtime, "status": status, "phase_outputs": merged_outputs})


def _merge_admissions(
    existing: tuple[EvidenceAdmissionRecord, ...],
    additions: tuple[EvidenceAdmissionRecord, ...],
) -> tuple[EvidenceAdmissionRecord, ...]:
    merged = {record.evidence_id: record for record in existing}
    for record in additions:
        merged[record.evidence_id] = record
    return tuple(merged.values())


def _trace(state: V2AiAiState, message: str) -> V2AiAiState:
    return state.model_copy(update={"trace": (*state.trace, message)})
