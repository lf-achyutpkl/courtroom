from __future__ import annotations

from uuid import uuid4

from courtroom_engine.application.coaching import run_coaching
from courtroom_engine.application.deliberation import run_judicial_deliberation
from courtroom_engine.application.evaluation import run_evaluation
from courtroom_engine.application.examination import WitnessExaminationOutput
from courtroom_engine.application.planning import plan_party_strategy
from courtroom_engine.compiler import CaseCompiler
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.coaching import CoachingReport
from courtroom_engine.domain.deliberation import DeliberationReport
from courtroom_engine.domain.evaluation import EvaluationReport
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import (
    EvidenceAdmissionRecord,
    EvidenceAdmissionStatus,
    ExaminationMode,
    PhaseTransitionRecord,
    ProcedureState,
    TrialPhase,
)
from courtroom_engine.domain.strategy import PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
from courtroom_engine.fixtures import build_reference_case
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .witness_graph import WitnessExaminationState, build_witness_examination_graph


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
    case_package: CompiledCasePackage | None = None
    runtime: TrialRuntimeState | None = None
    status: str = "created"
    boundary_context_ids: list[str] = Field(default_factory=list)
    strategies: dict[str, PartyStrategy] = Field(default_factory=dict)
    witness_examinations: list[WitnessExaminationOutput] = Field(default_factory=list)
    selected_witness: SelectedWitness | None = None
    remaining_witness_keys: list[str] = Field(default_factory=list)
    completed_witness_keys: list[str] = Field(default_factory=list)
    latest_witness_result: WitnessExaminationOutput | None = None
    opening_commitments: tuple[str, ...] = ()
    closing_record: ClosingRecord | None = None
    trial_position_updates: list[TrialPositionUpdate] = Field(default_factory=list)
    deliberation: DeliberationReport | None = None
    evaluation: EvaluationReport | None = None
    coaching: CoachingReport | None = None
    learning_trace: LearningTraceRecord | None = None
    phase_outputs: dict[str, str] = Field(default_factory=dict)
    trace: tuple[str, ...] = Field(default_factory=tuple)


def initialize_session_node(state: V2AiAiState) -> V2AiAiState:
    case_package = CaseCompiler().compile(build_reference_case())
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
        "initialize_session loaded and compiled the deterministic reference case.",
    )


def analyze_case_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    summary = (
        "Case intelligence available: "
        f"{len(case_package.intelligence.material_fact_map.facts)} material facts, "
        f"{len(case_package.intelligence.case_gaps)} gaps."
    )
    event = _event(
        CourtroomEventType.CASE_ANALYZED,
        TrialPhase.CASE_INTELLIGENCE,
        summary,
    )
    updated_runtime = _transition_runtime(
        runtime.model_copy(update={"events": (*runtime.events, event)}),
        TrialPhase.STRATEGY,
        summary,
    )
    return _trace(
        _with_runtime(
            state,
            updated_runtime,
            "case_analyzed",
            {"analyze_case": summary},
        ),
        "analyze_case exposed precompiled deterministic case intelligence.",
    )


def plan_prosecution_case_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    side = _first_side(case_package)
    strategy = plan_party_strategy(case_package=case_package, state=runtime, side=side)
    summary = f"Planned deterministic {side.value} strategy {strategy.strategy_id}."
    event = _event(
        CourtroomEventType.STRATEGY_PLANNED,
        TrialPhase.STRATEGY,
        summary,
        cited=(strategy.strategy_id,),
    )
    return _trace(
        _store_strategy(
            state,
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
    strategy = plan_party_strategy(
        case_package=case_package,
        state=runtime,
        side=PartySide.DEFENSE,
    )
    summary = f"Planned deterministic defense strategy {strategy.strategy_id}."
    event = _event(
        CourtroomEventType.STRATEGY_PLANNED,
        TrialPhase.STRATEGY,
        summary,
        cited=(strategy.strategy_id,),
    )
    return _trace(
        _store_strategy(state, runtime, strategy, event, "plan_defense_case", summary),
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
        (
            "finalize_trial_plan stored a private strategy schedule without "
            "merging contexts."
        ),
    )


def run_opening_phase_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    first_side = _first_side(case_package)
    commitments = (
        (
            f"{first_side.value} will prove visible material facts through "
            "planned witnesses."
        ),
        "defense will test proof gaps and visible contradiction risks.",
    )
    summary = f"Opening phase recorded {len(commitments)} deterministic commitment(s)."
    event = _event(CourtroomEventType.OPENING_DELIVERED, TrialPhase.OPENING, summary)
    updated_runtime = _transition_runtime(
        runtime.model_copy(update={"events": (*runtime.events, event)}),
        TrialPhase.WITNESS_EXAMINATION,
        summary,
    )
    return _trace(
        _with_runtime(
            state.model_copy(update={"opening_commitments": commitments}),
            updated_runtime,
            "openings_complete",
            {"opening": summary},
        ),
        (
            "run_opening_phase stored deterministic opening commitments for "
            "later evaluation."
        ),
    )


def select_next_witness_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    if not state.remaining_witness_keys:
        summary = "Witness loop completed; no witness slots remain."
        updated_runtime = _transition_runtime(
            runtime,
            TrialPhase.CLOSING_RECORD,
            summary,
        )
        return _trace(
            _with_runtime(
                state.model_copy(update={"selected_witness": None}),
                updated_runtime,
                "witness_loop_complete",
                {"witness_loop": summary},
            ),
            summary,
        )
    next_key = state.remaining_witness_keys[0]
    strategy_key, witness_id = next_key.split(":", 1)
    strategy = state.strategies[strategy_key]
    witness_plan = next(
        plan for plan in strategy.witness_plans if plan.witness_id == witness_id
    )
    selected = SelectedWitness(
        witness_id=witness_id,
        calling_side=strategy.side,
        strategy_key=strategy_key,
        objective_ids=witness_plan.objective_ids,
        reason=(
            "Needed for deterministic objective(s) "
            f"{', '.join(witness_plan.objective_ids)}."
        ),
    )
    event = _event(
        CourtroomEventType.WITNESS_SELECTED,
        TrialPhase.WITNESS_EXAMINATION,
        f"Selected witness {witness_id} for {strategy.side.value}.",
        cited=(witness_id, *witness_plan.objective_ids),
    )
    updated_runtime = runtime.model_copy(update={"events": (*runtime.events, event)})
    return _trace(
        _with_runtime(
            state.model_copy(update={"selected_witness": selected}),
            updated_runtime,
            "witness_selected",
            {"select_next_witness": event.summary},
        ),
        selected.reason,
    )


def route_after_witness_selection(state: V2AiAiState) -> str:
    return "complete" if state.selected_witness is None else "examine"


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
    result = build_witness_examination_graph().invoke(
        WitnessExaminationState(
            case_package=case_package,
            runtime=scoped_runtime,
            strategy=strategy,
            witness_id=selected.witness_id,
        )
    )
    output = result["output"]
    if output is None:
        raise ValueError("witness examination graph completed without output")
    updated_runtime = runtime.model_copy(
        update={
            "events": (*runtime.events, *output.events),
            "public_event_summaries": (
                *runtime.public_event_summaries,
                *output.event_summaries,
            ),
        }
    )
    return _trace(
        _with_runtime(
            state.model_copy(
                update={
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
    new_admissions = tuple(
        EvidenceAdmissionRecord(
            evidence_id=plan.evidence_id,
            status=EvidenceAdmissionStatus.ADMITTED,
        )
        for plan in strategy.evidence_plans
        if plan.through_witness_id == selected.witness_id
    )
    admissions = _merge_admissions(
        runtime.procedure.evidence_admissions,
        new_admissions,
    )
    completed_objective_ids = (
        (output.objective_id,)
        if output.objective_status.value == "satisfied"
        else ()
    )
    position_update = TrialPositionUpdate(
        update_id=f"TPU-{len(state.trial_position_updates) + 1:03d}",
        witness_id=selected.witness_id,
        completed_objective_ids=completed_objective_ids,
        admitted_evidence_ids=tuple(record.evidence_id for record in new_admissions),
        summary=f"Updated trial position after {selected.witness_id}.",
    )
    event = _event(
        CourtroomEventType.OBJECTIVE_ASSESSED,
        TrialPhase.WITNESS_EXAMINATION,
        position_update.summary,
        cited=(*completed_objective_ids, *position_update.admitted_evidence_ids),
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
            "public_event_summaries": (
                *runtime.public_event_summaries,
                position_update.summary,
            ),
        }
    )
    remaining = state.remaining_witness_keys[1:]
    completed = [*state.completed_witness_keys, state.remaining_witness_keys[0]]
    return _trace(
        _with_runtime(
            state.model_copy(
                update={
                    "remaining_witness_keys": remaining,
                    "completed_witness_keys": completed,
                    "trial_position_updates": [
                        *state.trial_position_updates,
                        position_update,
                    ],
                }
            ),
            updated_runtime,
            "trial_position_updated",
            {"update_trial_position": position_update.summary},
        ),
        "update_trial_position refreshed evidence admissions and objective progress.",
    )


def prepare_closing_record_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    completed_objectives = tuple(
        dict.fromkeys(
            objective_id
            for update in state.trial_position_updates
            for objective_id in update.completed_objective_ids
        )
    )
    record = ClosingRecord(
        admitted_evidence_ids=runtime.admitted_evidence_ids,
        testimony_event_ids=tuple(
            str(event.event_id)
            for event in runtime.events
            if event.event_type == CourtroomEventType.WITNESS_ANSWERED
        ),
        completed_objective_ids=completed_objectives,
        unresolved_contradiction_ids=tuple(
            cited_id
            for event in runtime.events
            if event.event_type == CourtroomEventType.CONTRADICTION_DETECTED
            for cited_id in event.cited_object_ids
        ),
        opening_commitments=state.opening_commitments,
    )
    summary = (
        "Closing record prepared with "
        f"{len(record.admitted_evidence_ids)} admitted evidence item(s)."
    )
    event = _event(
        CourtroomEventType.EVIDENCE_UPDATED,
        TrialPhase.CLOSING_RECORD,
        summary,
    )
    updated_runtime = _transition_runtime(
        runtime.model_copy(update={"events": (*runtime.events, event)}),
        TrialPhase.CLOSING,
        summary,
    )
    return _trace(
        _with_runtime(
            state.model_copy(update={"closing_record": record}),
            updated_runtime,
            "closing_record_prepared",
            {"closing_record": summary},
        ),
        "prepare_closings built a structured deterministic closing record.",
    )


def run_closing_phase_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    if state.closing_record is None:
        raise ValueError("closing phase requires closing record")
    summary = (
        "Closing phase recorded from admitted evidence, completed objectives, "
        "and opening commitments."
    )
    event = _event(CourtroomEventType.CLOSING_DELIVERED, TrialPhase.CLOSING, summary)
    updated_runtime = _transition_runtime(
        runtime.model_copy(update={"events": (*runtime.events, event)}),
        TrialPhase.DELIBERATION,
        summary,
    )
    return _trace(
        _with_runtime(
            state,
            updated_runtime,
            "closings_complete",
            {"closing": summary},
        ),
        "run_closing_phase generated deterministic closing trace.",
    )


def run_deliberation_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    deliberation = run_judicial_deliberation(case_package=case_package, state=runtime)
    summary = (
        "Structured deliberation reached "
        f"{deliberation.verdict.outcome.value} verdict with "
        f"{len(deliberation.finalized_findings)} finding(s)."
    )
    event = _event(
        CourtroomEventType.DELIBERATION_COMPLETED,
        TrialPhase.DELIBERATION,
        summary,
        cited=(deliberation.verdict.verdict_id,),
    )
    updated_runtime = _transition_runtime(
        runtime.model_copy(update={"events": (*runtime.events, event)}),
        TrialPhase.EVALUATION,
        summary,
    )
    return _trace(
        _with_runtime(
            state.model_copy(update={"deliberation": deliberation}),
            updated_runtime,
            "deliberation_complete",
            {"deliberation": summary},
        ),
        "run_deliberation used deterministic structured judicial deliberation.",
    )


def run_evaluation_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    if state.deliberation is None:
        raise ValueError("evaluation requires deliberation report")
    evaluation = run_evaluation(
        case_package=case_package,
        state=runtime,
        strategies=tuple(state.strategies.values()),
        witness_examinations=tuple(state.witness_examinations),
        deliberation=state.deliberation,
    )
    summary = (
        "Evaluation completed with "
        f"{len(evaluation.observations)} grounded observation(s) and "
        f"{len(evaluation.missed_opportunities)} missed opportunity record(s)."
    )
    event = _event(
        CourtroomEventType.EVALUATION_COMPLETED,
        TrialPhase.EVALUATION,
        summary,
    )
    updated_runtime = runtime.model_copy(update={"events": (*runtime.events, event)})
    return _trace(
        _with_runtime(
            state.model_copy(update={"evaluation": evaluation}),
            updated_runtime,
            "evaluation_complete",
            {"evaluation": summary},
        ),
        "run_evaluation executed deterministic evaluator pipeline.",
    )


def generate_coaching_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    if state.evaluation is None:
        raise ValueError("coaching requires evaluation report")
    coaching = run_coaching(evaluation=state.evaluation)
    summary = (
        "Coaching completed with "
        f"{len(coaching.moments)} moment(s) and "
        f"{len(coaching.skill_profile_updates)} skill update(s)."
    )
    event = _event(
        CourtroomEventType.COACHING_COMPLETED,
        TrialPhase.EVALUATION,
        summary,
    )
    updated_runtime = runtime.model_copy(update={"events": (*runtime.events, event)})
    return _trace(
        _with_runtime(
            state.model_copy(update={"coaching": coaching}),
            updated_runtime,
            "coaching_complete",
            {"coaching": summary},
        ),
        "generate_coaching transformed evaluation observations without rescoring.",
    )


def persist_learning_trace_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    summary = "Persisted deterministic in-memory learning trace for inspection."
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


def build_ai_ai_trial_graph():
    builder = StateGraph(V2AiAiState)
    builder.add_node("initialize_session", initialize_session_node)
    builder.add_node("analyze_case", analyze_case_node)
    builder.add_node("plan_prosecution_case", plan_prosecution_case_node)
    builder.add_node("plan_defense_case", plan_defense_case_node)
    builder.add_node("finalize_trial_plan", finalize_trial_plan_node)
    builder.add_node("run_opening_phase", run_opening_phase_node)
    builder.add_node("select_next_witness", select_next_witness_node)
    builder.add_node("run_witness_examination", run_witness_examination_node)
    builder.add_node("update_trial_position", update_trial_position_node)
    builder.add_node("prepare_closings", prepare_closing_record_node)
    builder.add_node("run_closing_phase", run_closing_phase_node)
    builder.add_node("run_deliberation", run_deliberation_node)
    builder.add_node("run_evaluation", run_evaluation_node)
    builder.add_node("generate_coaching", generate_coaching_node)
    builder.add_node("persist_learning_trace", persist_learning_trace_node)
    builder.add_edge(START, "initialize_session")
    builder.add_edge("initialize_session", "analyze_case")
    builder.add_edge("analyze_case", "plan_prosecution_case")
    builder.add_edge("plan_prosecution_case", "plan_defense_case")
    builder.add_edge("plan_defense_case", "finalize_trial_plan")
    builder.add_edge("finalize_trial_plan", "run_opening_phase")
    builder.add_edge("run_opening_phase", "select_next_witness")
    builder.add_conditional_edges(
        "select_next_witness",
        route_after_witness_selection,
        {
            "examine": "run_witness_examination",
            "complete": "prepare_closings",
        },
    )
    builder.add_edge("run_witness_examination", "update_trial_position")
    builder.add_edge("update_trial_position", "select_next_witness")
    builder.add_edge("prepare_closings", "run_closing_phase")
    builder.add_edge("run_closing_phase", "run_deliberation")
    builder.add_edge("run_deliberation", "run_evaluation")
    builder.add_edge("run_evaluation", "generate_coaching")
    builder.add_edge("generate_coaching", "persist_learning_trace")
    builder.add_edge("persist_learning_trace", END)
    return builder.compile()


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


def _require_latest_witness_result(state: V2AiAiState) -> WitnessExaminationOutput:
    if state.latest_witness_result is None:
        raise ValueError("trial position update requires latest witness result")
    return state.latest_witness_result


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
        update={
            "events": (*runtime.events, event),
            "party_strategies": tuple(strategies.values()),
        }
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
    transition = PhaseTransitionRecord(
        from_phase=current_phase,
        to_phase=phase,
        reason=summary,
    )
    procedure = runtime.procedure.model_copy(
        update={
            "phase": phase,
            "transitions": (*runtime.procedure.transitions, transition),
        }
    )
    return runtime.model_copy(
        update={
            "phase": phase.value,
            "procedure": procedure,
            "public_event_summaries": (*runtime.public_event_summaries, summary),
        }
    )


def _merge_admissions(
    existing: tuple[EvidenceAdmissionRecord, ...],
    new: tuple[EvidenceAdmissionRecord, ...],
) -> tuple[EvidenceAdmissionRecord, ...]:
    by_id = {record.evidence_id: record for record in existing}
    by_id.update({record.evidence_id: record for record in new})
    return tuple(by_id.values())


def _with_runtime(
    state: V2AiAiState,
    runtime: TrialRuntimeState,
    status: str,
    phase_output: dict[str, str],
) -> V2AiAiState:
    return state.model_copy(
        update={
            "runtime": runtime,
            "status": status,
            "phase_outputs": {**state.phase_outputs, **phase_output},
        }
    )


def _trace(state: V2AiAiState, message: str) -> V2AiAiState:
    return state.model_copy(update={"trace": (*state.trace, message)})
