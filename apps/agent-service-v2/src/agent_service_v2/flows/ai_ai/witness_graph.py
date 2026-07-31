from __future__ import annotations

from courtroom_engine.application.examination import (
    WitnessAnswerValidation,
    WitnessExaminationOutput,
    validate_witness_answer,
)
from courtroom_engine.application.planning import (
    build_question_execution_brief,
    build_tactical_action_plan,
)
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


def initialize_examination_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    return _trace(
        state.model_copy(update={"status": "examination_initialized"}),
        f"Initialized {state.mode.value} examination for {state.witness_id}.",
    )


def select_objective_node(state: WitnessExaminationState) -> WitnessExaminationState:
    objective = state.strategy.objectives[0]
    return _trace(
        state.model_copy(
            update={
                "active_objective_id": objective.objective_id,
                "objective_status": ObjectiveStatus.ACTIVE,
                "status": "objective_selected",
            }
        ),
        f"Selected objective {objective.objective_id}.",
    )


def plan_action_node(state: WitnessExaminationState) -> WitnessExaminationState:
    action = build_tactical_action_plan(state.strategy, state.witness_id)
    return _trace(
        state.model_copy(
            update={"tactical_action": action, "status": "action_planned"}
        ),
        f"Planned action {action.action_id} targeting {action.target_fact_ids}.",
    )


def validate_action_node(state: WitnessExaminationState) -> WitnessExaminationState:
    action = _require_action(state)
    missing_witness = action.target_witness_id != state.witness_id
    missing_targets = not action.target_fact_ids and not action.target_evidence_ids
    status = (
        "action_replan_required"
        if missing_witness or missing_targets
        else "action_valid"
    )
    reason = (
        "Action requires replanning."
        if status == "action_replan_required"
        else "Action passed deterministic validation."
    )
    return _trace(state.model_copy(update={"status": status}), reason)


def route_after_action_validation(state: WitnessExaminationState) -> str:
    if state.status == "action_replan_required":
        return "objective_complete"
    return "valid"


def generate_question_node(state: WitnessExaminationState) -> WitnessExaminationState:
    brief = build_question_execution_brief(_require_action(state))
    target = brief.allowed_fact_ids[0] if brief.allowed_fact_ids else "the key fact"
    question = f"What can you tell the court about {target}?"
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
                "question_text": question,
                "events": (*state.events, event),
                "status": "question_generated",
            }
        ),
        f"Generated deterministic question for {brief.objective_id}.",
    )


def objection_decision_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    decision = "no_objection"
    return _trace(
        state.model_copy(
            update={"objection_decision": decision, "status": "objection_decided"}
        ),
        "Opponent made deterministic no-objection decision.",
    )


def route_after_objection_decision(state: WitnessExaminationState) -> str:
    return "object" if state.objection_decision == "object" else "no_objection"


def judge_ruling_node(state: WitnessExaminationState) -> WitnessExaminationState:
    return _trace(
        state.model_copy(
            update={
                "ruling_outcome": RulingOutcome.OVERRULED,
                "status": "ruling_entered",
            }
        ),
        "Judge entered deterministic overruled ruling.",
    )


def route_after_ruling(state: WitnessExaminationState) -> str:
    if state.ruling_outcome == RulingOutcome.REPHRASE:
        return "sustained_rephrase"
    if state.ruling_outcome == RulingOutcome.SUSTAINED:
        return "sustained_replan"
    return "overruled"


def witness_answer_node(state: WitnessExaminationState) -> WitnessExaminationState:
    brief = _require_brief(state)
    atom = next(
        (
            atom
            for atom in state.case_package.witness_knowledge
            if atom.witness_id == brief.target_witness_id
            and any(
                fact_id in brief.allowed_fact_ids
                for fact_id in atom.related_fact_ids
            )
        ),
        None,
    )
    answer = (
        "I do not have personal knowledge of that point."
        if atom is None
        else atom.text
    )
    return _trace(
        state.model_copy(update={"answer_text": answer, "status": "witness_answered"}),
        (
            "Witness answered from deterministic knowledge boundary for "
            f"{state.witness_id}."
        ),
    )


def validate_witness_answer_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    brief = _require_brief(state)
    validation = validate_witness_answer(
        case_package=state.case_package,
        witness_id=state.witness_id,
        answer_text=state.answer_text,
        allowed_fact_ids=brief.allowed_fact_ids,
    )
    event = CourtroomEvent(
        event_type=CourtroomEventType.WITNESS_ANSWERED,
        phase=state.runtime.procedure.phase,
        summary=f"Witness answer validation: {validation.status.value}.",
        cited_object_ids=validation.supported_knowledge_ids,
    )
    return _trace(
        state.model_copy(
            update={
                "answer_validation": validation,
                "events": (*state.events, event),
                "status": f"answer_{validation.status.value}",
            }
        ),
        validation.message,
    )


def route_after_witness_validation(state: WitnessExaminationState) -> str:
    validation = _require_validation(state)
    if validation.status == AnswerValidationStatus.HALLUCINATION:
        return "flag"
    return "valid"


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
        "Updated deterministic evidence trace from accepted answer.",
    )


def detect_new_contradictions_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    validation = _require_validation(state)
    cited = validation.contradiction_ids
    if not cited:
        return _trace(
            state.model_copy(update={"status": "contradictions_checked"}),
            "No new contradiction surfaced in deterministic pass.",
        )
    event = CourtroomEvent(
        event_type=CourtroomEventType.CONTRADICTION_DETECTED,
        phase=state.runtime.procedure.phase,
        summary=f"Contradiction available from {state.witness_id}.",
        cited_object_ids=cited,
    )
    return _trace(
        state.model_copy(
            update={
                "events": (*state.events, event),
                "status": "contradiction_detected",
            }
        ),
        f"Detected contradiction(s) {cited}.",
    )


def assess_objective_progress_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    validation = _require_validation(state)
    objective_status = (
        ObjectiveStatus.SATISFIED
        if validation.status
        in {
            AnswerValidationStatus.SUPPORTED,
            AnswerValidationStatus.INTENTIONAL_CONTRADICTION,
        }
        else ObjectiveStatus.ACTIVE
    )
    objective_id = state.active_objective_id or _require_brief(state).objective_id
    event = CourtroomEvent(
        event_type=CourtroomEventType.OBJECTIVE_ASSESSED,
        phase=state.runtime.procedure.phase,
        summary=f"Objective {objective_id} is {objective_status.value}.",
        cited_object_ids=(objective_id,),
    )
    return _trace(
        state.model_copy(
            update={
                "objective_status": objective_status,
                "events": (*state.events, event),
                "status": "objective_assessed",
            }
        ),
        f"Objective {objective_id} assessed as {objective_status.value}.",
    )


def route_after_objective_assessment(state: WitnessExaminationState) -> str:
    return "finish_section"


def transition_examination_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    return _trace(
        state.model_copy(update={"status": "examination_transition_complete"}),
        "Deterministic slice completes this witness section.",
    )


def route_examination_transition(state: WitnessExaminationState) -> str:
    return "complete"


def finalize_witness_node(
    state: WitnessExaminationState,
) -> WitnessExaminationState:
    brief = _require_brief(state)
    validation = _require_validation(state)
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
        event_summaries=tuple(event.summary for event in state.events),
        events=state.events,
    )
    return _trace(
        state.model_copy(
            update={"output": output, "status": "witness_examination_complete"}
        ),
        f"Finalized witness result for {state.witness_id}.",
    )


def build_witness_examination_graph():
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
