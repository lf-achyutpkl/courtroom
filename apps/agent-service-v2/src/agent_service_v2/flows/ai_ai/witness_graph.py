from __future__ import annotations

from typing import Any

from courtroom_engine.application.examination import (
    WitnessAnswerValidation,
    WitnessExaminationOutput,
    validate_witness_answer,
)
from courtroom_engine.application.planning import build_question_execution_brief
from courtroom_engine.context import QuestionExecutionBriefDTO, TacticalActionPlanDTO
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import (
    AnswerValidationStatus,
    ExaminationMode,
    RulingOutcome,
)
from courtroom_engine.domain.strategy import ObjectiveStatus, PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
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
    ExaminationActionReview,
    ExaminationObjectiveDecision,
    GeneratedQuestion,
    ObjectiveProgressAssessment,
    PlannedExaminationAction,
    ProceduralChallengeDecision,
    ProceduralDecision,
    RuntimeContradictionResult,
    WitnessAnswer,
    WitnessAnswerReview,
    WitnessResult,
)


class WitnessExaminationState(BaseModel):
    case_package: CompiledCasePackage
    runtime: TrialRuntimeState
    strategy: PartyStrategy
    witness_id: str
    mode: ExaminationMode = ExaminationMode.DIRECT
    active_objective_id: str | None = None
    tactical_action: TacticalActionPlanDTO | None = None
    question_brief: QuestionExecutionBriefDTO | None = None
    question_text: str = ""
    objection_decision: str = "none"
    ruling_outcome: RulingOutcome | None = None
    answer_text: str = ""
    answer_validation: WitnessAnswerValidation | None = None
    objective_status: ObjectiveStatus = ObjectiveStatus.PLANNED
    output: WitnessExaminationOutput | None = None
    status: str = "created"
    trace: tuple[str, ...] = Field(default_factory=tuple)
    events: tuple[CourtroomEvent, ...] = Field(default_factory=tuple)
    prompt_runs: tuple[PromptRunRecord, ...] = Field(default_factory=tuple)
    node_failure: NodeFailureRecord | None = None


class GraphNodeExecutionError(RuntimeError):
    def __init__(
        self,
        node_name: str,
        failure: NodeFailureRecord,
        *,
        state: WitnessExaminationState | None,
    ) -> None:
        super().__init__(f"{node_name}: {failure.message}")
        self.node_name = node_name
        self.failure = failure
        self.state = state


def initialize_examination_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    return _trace(
        state.model_copy(update={"status": "examination_initialized"}),
        f"Initialized {state.mode.value} examination for {state.witness_id}.",
    )


def build_witness_examination_graph(
    prompt_executor: StructuredPromptExecutor | None = None,
):
    def select_objective_node(state: WitnessExaminationState) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "select_objective")
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="select_objective",
            prompt_id=PromptId.SELECT_EXAMINATION_OBJECTIVE,
            context={
                "witness_id": state.witness_id,
                "mode": state.mode.value,
                "strategy": state.strategy,
                "runtime": state.runtime,
            },
            schema=ExaminationObjectiveDecision,
            semantic_validator=lambda output: _validate_objective_choice(
                state.strategy, output
            ),
            prompt_runs=state.prompt_runs,
        )
        return _trace(
            state.model_copy(
                update={
                    "active_objective_id": result.objective_id,
                    "objective_status": ObjectiveStatus.ACTIVE,
                    "prompt_runs": prompt_runs,
                    "status": "objective_selected",
                }
            ),
            f"Selected live objective {result.objective_id}.",
        )

    def plan_action_node(state: WitnessExaminationState) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "plan_action")
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="plan_action",
            prompt_id=PromptId.PLAN_EXAMINATION_ACTION,
            context={
                "witness_id": state.witness_id,
                "active_objective_id": state.active_objective_id,
                "strategy": state.strategy,
                "runtime": state.runtime,
                "latest_events": state.events,
            },
            schema=PlannedExaminationAction,
            semantic_validator=lambda output: _validate_planned_action(
                state, output
            ),
            prompt_runs=state.prompt_runs,
        )
        action = TacticalActionPlanDTO(
            action_id=result.action_id,
            objective_id=result.objective_id,
            action_type=result.action_type,
            target_fact_ids=result.target_fact_ids,
            target_evidence_ids=result.target_evidence_ids,
            target_witness_id=result.target_witness_id,
            expected_effect=result.expected_effect,
        )
        return _trace(
            state.model_copy(
                update={
                    "tactical_action": action,
                    "prompt_runs": prompt_runs,
                    "status": "action_planned",
                }
            ),
            f"Planned live action {action.action_id}.",
        )

    def validate_action_node(state: WitnessExaminationState) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "validate_action")
        action = _require_action(state)
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="validate_action",
            prompt_id=PromptId.REVIEW_EXAMINATION_ACTION,
            context={
                "witness_id": state.witness_id,
                "active_objective_id": state.active_objective_id,
                "tactical_action": action,
                "strategy": state.strategy,
                "runtime": state.runtime,
            },
            schema=ExaminationActionReview,
            semantic_validator=_validate_approved_review,
            prompt_runs=state.prompt_runs,
        )
        status = "action_valid" if result.approved else "action_replan_required"
        return _trace(
            state.model_copy(update={"prompt_runs": prompt_runs, "status": status}),
            "Live action review accepted the tactical action."
            if result.approved
            else "Live action review rejected the tactical action.",
        )

    def generate_question_node(state: WitnessExaminationState) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "generate_question")
        action = _require_action(state)
        brief = build_question_execution_brief(action)
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="generate_question",
            prompt_id=PromptId.DRAFT_QUESTION,
            context={
                "witness_id": state.witness_id,
                "question_brief": brief,
                "tactical_action": action,
                "runtime": state.runtime,
            },
            schema=GeneratedQuestion,
            semantic_validator=lambda output: _validate_generated_question(
                brief, output
            ),
            prompt_runs=state.prompt_runs,
        )
        event = CourtroomEvent(
            event_type=CourtroomEventType.QUESTION_ASKED,
            phase=state.runtime.procedure.phase,
            summary=f"Question asked of {state.witness_id} for {brief.objective_id}.",
            cited_object_ids=(brief.action_id, *brief.allowed_fact_ids),
        )
        return _trace(
            state.model_copy(
                update={
                    "question_brief": brief,
                    "question_text": result.question_text,
                    "events": (*state.events, event),
                    "prompt_runs": prompt_runs,
                    "status": "question_generated",
                }
            ),
            f"Generated live question for {brief.objective_id}.",
        )

    def objection_decision_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "objection_decision")
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="objection_decision",
            prompt_id=PromptId.PROCEDURAL_CHALLENGE_DECISION,
            context={
                "question_text": state.question_text,
                "question_brief": _require_brief(state),
                "runtime": state.runtime,
                "strategy": state.strategy,
            },
            schema=ProceduralChallengeDecision,
            prompt_runs=state.prompt_runs,
        )
        decision = "object" if result.challenge else "no_objection"
        return _trace(
            state.model_copy(
                update={
                    "objection_decision": decision,
                    "prompt_runs": prompt_runs,
                    "status": "objection_decided",
                }
            ),
            "Live objection decision completed.",
        )

    def judge_ruling_node(state: WitnessExaminationState) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "judge_ruling")
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="judge_ruling",
            prompt_id=PromptId.PROCEDURAL_DECISION,
            context={
                "question_text": state.question_text,
                "question_brief": _require_brief(state),
                "objection_decision": state.objection_decision,
                "runtime": state.runtime,
            },
            schema=ProceduralDecision,
            semantic_validator=_validate_procedural_decision,
            prompt_runs=state.prompt_runs,
        )
        outcome_map = {
            "overruled": RulingOutcome.OVERRULED,
            "sustained": RulingOutcome.SUSTAINED,
            "rephrase": RulingOutcome.REPHRASE,
        }
        return _trace(
            state.model_copy(
                update={
                    "ruling_outcome": outcome_map[result.outcome],
                    "prompt_runs": prompt_runs,
                    "status": "ruling_entered",
                }
            ),
            f"Judge entered live {result.outcome} ruling.",
        )

    def witness_answer_node(state: WitnessExaminationState) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "witness_answer")
        brief = _require_brief(state)
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="witness_answer",
            prompt_id=PromptId.WITNESS_ANSWER,
            context={
                "witness_id": state.witness_id,
                "question_text": state.question_text,
                "question_brief": brief,
                "runtime": state.runtime,
                "witness_knowledge": tuple(
                    atom
                    for atom in state.case_package.witness_knowledge
                    if atom.witness_id == state.witness_id
                ),
            },
            schema=WitnessAnswer,
            semantic_validator=_validate_witness_answer_text,
            prompt_runs=state.prompt_runs,
        )
        return _trace(
            state.model_copy(
                update={
                    "answer_text": result.answer_text,
                    "prompt_runs": prompt_runs,
                    "status": "witness_answered",
                }
            ),
            f"Witness answered live for {state.witness_id}.",
        )

    def validate_witness_answer_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "validate_witness_answer")
        brief = _require_brief(state)
        grounded = validate_witness_answer(
            case_package=state.case_package,
            witness_id=state.witness_id,
            answer_text=state.answer_text,
            allowed_fact_ids=brief.allowed_fact_ids,
        )
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="validate_witness_answer",
            prompt_id=PromptId.REVIEW_WITNESS_ANSWER,
            context={
                "question_text": state.question_text,
                "answer_text": state.answer_text,
                "question_brief": brief,
                "grounded_validation": grounded,
            },
            schema=WitnessAnswerReview,
            semantic_validator=lambda output: _validate_answer_review(grounded, output),
            prompt_runs=state.prompt_runs,
        )
        event = CourtroomEvent(
            event_type=CourtroomEventType.WITNESS_ANSWERED,
            phase=state.runtime.procedure.phase,
            summary=f"Witness answer validation: {result.status.value}.",
            cited_object_ids=grounded.supported_knowledge_ids,
        )
        validation = grounded.model_copy(
            update={"status": result.status, "message": result.message}
        )
        return _trace(
            state.model_copy(
                update={
                    "answer_validation": validation,
                    "events": (*state.events, event),
                    "prompt_runs": prompt_runs,
                    "status": f"answer_{validation.status.value}",
                }
            ),
            validation.message,
        )

    def update_evidence_state_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        brief = _require_brief(state)
        event = CourtroomEvent(
            event_type=CourtroomEventType.EVIDENCE_UPDATED,
            phase=state.runtime.procedure.phase,
            summary=f"Evidence state updated for {state.witness_id}.",
            cited_object_ids=brief.allowed_evidence_ids,
        )
        return _trace(
            state.model_copy(
                update={"events": (*state.events, event), "status": "evidence_updated"}
            ),
            "Updated evidence trace after accepted answer.",
        )

    def detect_new_contradictions_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "detect_new_contradictions")
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="detect_new_contradictions",
            prompt_id=PromptId.DETECT_RUNTIME_CONTRADICTIONS,
            context={
                "answer_validation": _require_validation(state),
                "answer_text": state.answer_text,
                "events": state.events,
                "runtime": state.runtime,
            },
            schema=RuntimeContradictionResult,
            semantic_validator=lambda output: _validate_runtime_contradictions(
                state.case_package, output
            ),
            prompt_runs=state.prompt_runs,
        )
        if not result.contradiction_ids:
            return _trace(
                state.model_copy(
                    update={
                        "prompt_runs": prompt_runs,
                        "status": "contradictions_checked",
                    }
                ),
                "No new contradiction surfaced in live pass.",
            )
        event = CourtroomEvent(
            event_type=CourtroomEventType.CONTRADICTION_DETECTED,
            phase=state.runtime.procedure.phase,
            summary=f"Contradiction available from {state.witness_id}.",
            cited_object_ids=result.contradiction_ids,
        )
        return _trace(
            state.model_copy(
                update={
                    "events": (*state.events, event),
                    "prompt_runs": prompt_runs,
                    "status": "contradiction_detected",
                }
            ),
            f"Detected contradiction(s) {result.contradiction_ids}.",
        )

    def assess_objective_progress_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "assess_objective_progress")
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="assess_objective_progress",
            prompt_id=PromptId.ASSESS_OBJECTIVE_PROGRESS,
            context={
                "active_objective_id": state.active_objective_id,
                "answer_validation": _require_validation(state),
                "events": state.events,
                "runtime": state.runtime,
            },
            schema=ObjectiveProgressAssessment,
            semantic_validator=_validate_objective_progress,
            prompt_runs=state.prompt_runs,
        )
        objective_id = state.active_objective_id or _require_brief(state).objective_id
        event = CourtroomEvent(
            event_type=CourtroomEventType.OBJECTIVE_ASSESSED,
            phase=state.runtime.procedure.phase,
            summary=f"Objective {objective_id} is {result.objective_status.value}.",
            cited_object_ids=(objective_id,),
        )
        return _trace(
            state.model_copy(
                update={
                    "objective_status": result.objective_status,
                    "events": (*state.events, event),
                    "prompt_runs": prompt_runs,
                    "status": result.next_step,
                }
            ),
            result.reason,
        )

    def transition_examination_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        return _trace(
            state.model_copy(update={"status": "examination_transition_complete"}),
            "Witness section transition complete.",
        )

    def finalize_witness_node(
        state: WitnessExaminationState,
    ) -> WitnessExaminationState:
        executor = _require_executor(prompt_executor, "finalize_witness")
        brief = _require_brief(state)
        validation = _require_validation(state)
        result, prompt_runs = _invoke_prompt(
            executor,
            node_name="finalize_witness",
            prompt_id=PromptId.SUMMARIZE_WITNESS_RESULT,
            context={
                "witness_id": state.witness_id,
                "question_text": state.question_text,
                "answer_text": state.answer_text,
                "answer_validation": validation,
                "events": state.events,
            },
            schema=WitnessResult,
            prompt_runs=state.prompt_runs,
        )
        output = WitnessExaminationOutput(
            examination_id=f"EXAM-{state.witness_id}-{state.mode.value.upper()}",
            witness_id=state.witness_id,
            mode=state.mode,
            objective_id=brief.objective_id,
            tactical_action=_require_action(state),
            question_brief=brief,
            question_text=state.question_text,
            answer_text=state.answer_text,
            answer_validation=validation,
            objective_status=state.objective_status,
            event_summaries=(*tuple(event.summary for event in state.events), result.summary),
            events=state.events,
        )
        return _trace(
            state.model_copy(
                update={
                    "output": output,
                    "prompt_runs": prompt_runs,
                    "status": "witness_examination_complete",
                }
            ),
            f"Finalized live witness result for {state.witness_id}.",
        )

    builder = StateGraph(WitnessExaminationState)
    builder.add_node("initialize_examination", initialize_examination_node)
    builder.add_node("select_objective", select_objective_node)
    builder.add_node("plan_action", plan_action_node)
    builder.add_node("validate_action", validate_action_node)
    builder.add_node("generate_question", generate_question_node)
    builder.add_node("objection_decision", objection_decision_node)
    builder.add_node("judge_ruling", judge_ruling_node)
    builder.add_node("witness_answer", witness_answer_node)
    builder.add_node("validate_witness_answer", validate_witness_answer_node)
    builder.add_node("update_evidence_state", update_evidence_state_node)
    builder.add_node("detect_new_contradictions", detect_new_contradictions_node)
    builder.add_node("assess_objective_progress", assess_objective_progress_node)
    builder.add_node("transition_examination", transition_examination_node)
    builder.add_node("finalize_witness", finalize_witness_node)
    builder.add_edge(START, "initialize_examination")
    builder.add_edge("initialize_examination", "select_objective")
    builder.add_edge("select_objective", "plan_action")
    builder.add_edge("plan_action", "validate_action")
    builder.add_conditional_edges(
        "validate_action",
        route_after_action_validation,
        {
            "valid": "generate_question",
            "replan": "plan_action",
            "objective_complete": "transition_examination",
        },
    )
    builder.add_edge("generate_question", "objection_decision")
    builder.add_conditional_edges(
        "objection_decision",
        route_after_objection_decision,
        {
            "no_objection": "witness_answer",
            "object": "judge_ruling",
        },
    )
    builder.add_conditional_edges(
        "judge_ruling",
        route_after_ruling,
        {
            "overruled": "witness_answer",
            "sustained_replan": "plan_action",
            "sustained_rephrase": "generate_question",
        },
    )
    builder.add_edge("witness_answer", "validate_witness_answer")
    builder.add_conditional_edges(
        "validate_witness_answer",
        route_after_witness_validation,
        {
            "valid": "update_evidence_state",
            "repair": "witness_answer",
            "flag": "update_evidence_state",
        },
    )
    builder.add_edge("update_evidence_state", "detect_new_contradictions")
    builder.add_edge("detect_new_contradictions", "assess_objective_progress")
    builder.add_conditional_edges(
        "assess_objective_progress",
        route_after_objective_assessment,
        {
            "continue": "plan_action",
            "change_objective": "select_objective",
            "finish_section": "transition_examination",
        },
    )
    builder.add_conditional_edges(
        "transition_examination",
        route_examination_transition,
        {
            "direct": "select_objective",
            "cross": "select_objective",
            "redirect": "select_objective",
            "recross": "select_objective",
            "complete": "finalize_witness",
        },
    )
    builder.add_edge("finalize_witness", END)
    return builder.compile()


def route_after_action_validation(state: WitnessExaminationState) -> str:
    if state.status == "action_replan_required":
        return "replan"
    if state.status == "objective_complete":
        return "objective_complete"
    return "valid"


def route_after_objection_decision(state: WitnessExaminationState) -> str:
    return "object" if state.objection_decision == "object" else "no_objection"


def route_after_ruling(state: WitnessExaminationState) -> str:
    if state.ruling_outcome == RulingOutcome.REPHRASE:
        return "sustained_rephrase"
    if state.ruling_outcome == RulingOutcome.SUSTAINED:
        return "sustained_replan"
    return "overruled"


def route_after_witness_validation(state: WitnessExaminationState) -> str:
    validation = _require_validation(state)
    if validation.status == AnswerValidationStatus.HALLUCINATION:
        return "flag"
    return "valid"


def route_after_objective_assessment(state: WitnessExaminationState) -> str:
    next_step = state.status
    if next_step == "continue":
        return "continue"
    if next_step == "change_objective":
        return "change_objective"
    return "finish_section"


def route_examination_transition(state: WitnessExaminationState) -> str:
    return "complete"


def _invoke_prompt(
    executor: StructuredPromptExecutor,
    *,
    node_name: str,
    prompt_id: PromptId,
    context: Any,
    schema: type[Any],
    prompt_runs: tuple[PromptRunRecord, ...],
    semantic_validator: Any = None,
) -> tuple[Any, tuple[PromptRunRecord, ...]]:
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
        raise GraphNodeExecutionError(
            node_name,
            failure,
            state=context if isinstance(context, WitnessExaminationState) else None,
        ) from exc
    run = PromptRunRecord(
        node_name=node_name,
        prompt_id=prompt_id.value,
        outcome=result.outcome.value,
        attempts=result.attempts,
        response_id=result.response_id,
        cached_tokens=result.usage.cached_tokens,
        cache_write_tokens=result.usage.cache_write_tokens,
    )
    return result.output, (*prompt_runs, run)


def _require_executor(
    executor: StructuredPromptExecutor | None,
    node_name: str,
) -> StructuredPromptExecutor:
    if executor is None:
        raise RuntimeError(
            f"{node_name} requires a configured prompt executor for live execution"
        )
    return executor


def _validate_objective_choice(
    strategy: PartyStrategy, output: ExaminationObjectiveDecision
) -> SemanticValidationResult:
    valid_ids = {objective.objective_id for objective in strategy.objectives}
    if output.objective_id in valid_ids:
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = f"Unknown objective id {output.objective_id!r}."
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_planned_action(
    state: WitnessExaminationState, output: PlannedExaminationAction
) -> SemanticValidationResult:
    if output.target_witness_id not in {None, state.witness_id}:
        message = "Planned action targeted the wrong witness."
        return SemanticValidationResult(
            accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
            validation_feedback=(message,),
            error_message=message,
        )
    if (
        output.objective_id != state.active_objective_id
        or (not output.target_fact_ids and not output.target_evidence_ids)
    ):
        message = "Planned action must advance the active objective with a real target."
        return SemanticValidationResult(
            accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
            validation_feedback=(message,),
            error_message=message,
        )
    return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)


def _validate_approved_review(review: ExaminationActionReview) -> SemanticValidationResult:
    if review.approved:
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = review.messages[0] if review.messages else "Review rejected the action."
    return SemanticValidationResult(
        accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_generated_question(
    brief: QuestionExecutionBriefDTO, output: GeneratedQuestion
) -> SemanticValidationResult:
    if output.question_text.strip():
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = f"Question text for {brief.objective_id} cannot be empty."
    return SemanticValidationResult(
        accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_procedural_decision(
    decision: ProceduralDecision,
) -> SemanticValidationResult:
    if decision.outcome in {"overruled", "sustained", "rephrase"}:
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = f"Unsupported ruling outcome {decision.outcome!r}."
    return SemanticValidationResult(
        accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_witness_answer_text(answer: WitnessAnswer) -> SemanticValidationResult:
    if answer.answer_text.strip():
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = "Witness answer cannot be empty."
    return SemanticValidationResult(
        accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_answer_review(
    grounded: WitnessAnswerValidation, review: WitnessAnswerReview
) -> SemanticValidationResult:
    if review.status == grounded.status:
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = (
        f"Answer review status {review.status.value} did not match grounded "
        f"status {grounded.status.value}."
    )
    return SemanticValidationResult(
        accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_runtime_contradictions(
    case_package: CompiledCasePackage, result: RuntimeContradictionResult
) -> SemanticValidationResult:
    valid_ids = {
        contradiction.contradiction_id
        for contradiction in case_package.intelligence.contradiction_graph.contradictions
    }
    if all(contradiction_id in valid_ids for contradiction_id in result.contradiction_ids):
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = "Runtime contradiction output referenced an unknown contradiction id."
    return SemanticValidationResult(
        accepted=False,
            outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _validate_objective_progress(
    result: ObjectiveProgressAssessment,
) -> SemanticValidationResult:
    if result.next_step in {"continue", "change_objective", "finish_section"}:
        return SemanticValidationResult(accepted=True, outcome=InvocationOutcome.SUCCESS)
    message = f"Unsupported objective transition {result.next_step!r}."
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


def _require_action(state: WitnessExaminationState) -> TacticalActionPlanDTO:
    if state.tactical_action is None:
        raise ValueError("witness graph requires a planned tactical action")
    return state.tactical_action


def _require_brief(state: WitnessExaminationState) -> QuestionExecutionBriefDTO:
    if state.question_brief is None:
        raise ValueError("witness graph requires a question execution brief")
    return state.question_brief


def _require_validation(state: WitnessExaminationState) -> WitnessAnswerValidation:
    if state.answer_validation is None:
        raise ValueError("witness graph requires answer validation")
    return state.answer_validation


def _trace(state: WitnessExaminationState, message: str) -> WitnessExaminationState:
    return state.model_copy(update={"trace": (*state.trace, message)})
