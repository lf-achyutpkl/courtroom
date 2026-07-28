from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from courtroom_engine.application.examination import (
    WitnessExaminationOutput,
    run_witness_examination,
)
from courtroom_engine.application.planning import plan_party_strategy
from courtroom_engine.compiler import CaseCompiler
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import (
    EvidenceAdmissionRecord,
    EvidenceAdmissionStatus,
    ExaminationMode,
    ProcedureState,
    TrialPhase,
)
from courtroom_engine.domain.strategy import PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
from courtroom_engine.fixtures import build_reference_case


class V2AiAiState(BaseModel):
    case_package: CompiledCasePackage | None = None
    runtime: TrialRuntimeState | None = None
    status: str = "created"
    boundary_context_ids: list[str] = Field(default_factory=list)
    strategies: dict[str, PartyStrategy] = Field(default_factory=dict)
    witness_examinations: list[WitnessExaminationOutput] = Field(default_factory=list)
    phase_outputs: dict[str, str] = Field(default_factory=dict)


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
    return state.model_copy(
        update={
            "case_package": case_package,
            "runtime": runtime,
            "status": "initialized",
            "phase_outputs": {"initialize_session": event.summary},
        }
    )


def analyze_case_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    summary = (
        "Case intelligence available: "
        f"{len(case_package.intelligence.material_fact_map.facts)} material facts, "
        f"{len(case_package.intelligence.case_gaps)} gaps."
    )
    event = _event(CourtroomEventType.CASE_ANALYZED, TrialPhase.CASE_INTELLIGENCE, summary)
    return _with_runtime(
        state,
        runtime.with_phase(TrialPhase.STRATEGY, summary).model_copy(
            update={"events": (*runtime.events, event)}
        ),
        "case_analyzed",
        {"analyze_case": summary},
    )


def plan_sides_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    first_side = _first_side(case_package)
    first_strategy = plan_party_strategy(
        case_package=case_package,
        state=runtime,
        side=first_side,
    )
    defense_strategy = plan_party_strategy(
        case_package=case_package,
        state=runtime,
        side=PartySide.DEFENSE,
    )
    strategies = {
        first_strategy.side.value: first_strategy,
        defense_strategy.side.value: defense_strategy,
    }
    summary = (
        "Planned private strategies for "
        f"{first_strategy.side.value} and defense."
    )
    event = _event(
        CourtroomEventType.STRATEGY_PLANNED,
        TrialPhase.STRATEGY,
        summary,
        cited=(first_strategy.strategy_id, defense_strategy.strategy_id),
    )
    updated_runtime = runtime.with_phase(TrialPhase.OPENING, summary).model_copy(
        update={
            "events": (*runtime.events, event),
            "party_strategies": (first_strategy, defense_strategy),
        }
    )
    return _with_runtime(
        state.model_copy(update={"strategies": strategies}),
        updated_runtime,
        "strategies_planned",
        {"plan_sides": summary},
    )


def run_opening_phase_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    first_side = _first_side(case_package)
    summary = f"Opening phase recorded for {first_side.value} and defense."
    event = _event(CourtroomEventType.OPENING_DELIVERED, TrialPhase.OPENING, summary)
    updated_runtime = runtime.with_phase(TrialPhase.WITNESS_EXAMINATION, summary)
    updated_runtime = updated_runtime.model_copy(update={"events": (*runtime.events, event)})
    return _with_runtime(state, updated_runtime, "openings_complete", {"opening": summary})


def run_witness_loop_node(state: V2AiAiState) -> V2AiAiState:
    case_package, runtime = _require_initialized(state)
    outputs: list[WitnessExaminationOutput] = []
    events = list(runtime.events)
    summaries = list(runtime.public_event_summaries)
    admissions: list[EvidenceAdmissionRecord] = []
    for strategy in state.strategies.values():
        for witness_plan in sorted(strategy.witness_plans, key=lambda plan: plan.order):
            procedure = runtime.procedure.model_copy(
                update={
                    "phase": TrialPhase.WITNESS_EXAMINATION,
                    "current_witness_id": witness_plan.witness_id,
                    "examination_mode": ExaminationMode.DIRECT,
                }
            )
            scoped_runtime = runtime.model_copy(
                update={
                    "phase": TrialPhase.WITNESS_EXAMINATION.value,
                    "procedure": procedure,
                    "current_witness_id": witness_plan.witness_id,
                }
            )
            output = run_witness_examination(
                case_package=case_package,
                state=scoped_runtime,
                strategy=strategy,
                witness_id=witness_plan.witness_id,
            )
            outputs.append(output)
            events.extend(output.events)
            summaries.extend(output.event_summaries)
            admissions.extend(
                EvidenceAdmissionRecord(
                    evidence_id=evidence_plan.evidence_id,
                    status=EvidenceAdmissionStatus.ADMITTED,
                )
                for evidence_plan in strategy.evidence_plans
                if evidence_plan.through_witness_id == witness_plan.witness_id
            )
    unique_admissions = tuple({record.evidence_id: record for record in admissions}.values())
    summary = f"Witness loop completed with {len(outputs)} examination record(s)."
    event = _event(
        CourtroomEventType.EVIDENCE_UPDATED,
        TrialPhase.WITNESS_EXAMINATION,
        summary,
        cited=tuple(record.evidence_id for record in unique_admissions),
    )
    events.append(event)
    summaries.append(summary)
    procedure = runtime.procedure.model_copy(
        update={
            "phase": TrialPhase.CLOSING_RECORD,
            "current_witness_id": None,
            "evidence_admissions": unique_admissions,
        }
    )
    updated_runtime = runtime.model_copy(
        update={
            "phase": TrialPhase.CLOSING_RECORD.value,
            "procedure": procedure,
            "admitted_evidence_ids": procedure.admitted_evidence_ids,
            "events": tuple(events),
            "public_event_summaries": tuple(summaries),
        }
    )
    return _with_runtime(
        state.model_copy(update={"witness_examinations": outputs}),
        updated_runtime,
        "witness_loop_complete",
        {"witness_loop": summary},
    )


def prepare_closing_record_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    summary = (
        "Closing record prepared from admitted evidence "
        f"{tuple(runtime.admitted_evidence_ids)}."
    )
    event = _event(CourtroomEventType.EVIDENCE_UPDATED, TrialPhase.CLOSING_RECORD, summary)
    updated_runtime = runtime.with_phase(TrialPhase.CLOSING, summary).model_copy(
        update={"events": (*runtime.events, event)}
    )
    return _with_runtime(
        state,
        updated_runtime,
        "closing_record_prepared",
        {"closing_record": summary},
    )


def run_closing_phase_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    summary = "Closing phase recorded for both sides from the admitted record."
    event = _event(CourtroomEventType.CLOSING_DELIVERED, TrialPhase.CLOSING, summary)
    updated_runtime = runtime.with_phase(TrialPhase.DELIBERATION, summary).model_copy(
        update={"events": (*runtime.events, event)}
    )
    return _with_runtime(state, updated_runtime, "closings_complete", {"closing": summary})


def run_deliberation_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    summary = "Structured deliberation placeholder applied burden to admitted record."
    event = _event(
        CourtroomEventType.DELIBERATION_COMPLETED,
        TrialPhase.DELIBERATION,
        summary,
    )
    updated_runtime = runtime.with_phase(TrialPhase.EVALUATION, summary).model_copy(
        update={"events": (*runtime.events, event)}
    )
    return _with_runtime(
        state,
        updated_runtime,
        "deliberation_complete",
        {"deliberation": summary},
    )


def run_evaluation_node(state: V2AiAiState) -> V2AiAiState:
    _, runtime = _require_initialized(state)
    summary = "Evaluation placeholder recorded procedure, role, and strategy traces."
    event = _event(CourtroomEventType.EVALUATION_COMPLETED, TrialPhase.EVALUATION, summary)
    updated_runtime = runtime.with_phase(TrialPhase.COMPLETE, summary).model_copy(
        update={"events": (*runtime.events, event)}
    )
    return _with_runtime(state, updated_runtime, "evaluation_complete", {"evaluation": summary})


def build_v2_ai_ai_graph():
    builder = StateGraph(V2AiAiState)
    builder.add_node("initialize_session", initialize_session_node)
    builder.add_node("analyze_case", analyze_case_node)
    builder.add_node("plan_sides", plan_sides_node)
    builder.add_node("run_opening_phase", run_opening_phase_node)
    builder.add_node("run_witness_loop", run_witness_loop_node)
    builder.add_node("prepare_closing_record", prepare_closing_record_node)
    builder.add_node("run_closing_phase", run_closing_phase_node)
    builder.add_node("run_deliberation", run_deliberation_node)
    builder.add_node("run_evaluation", run_evaluation_node)
    builder.add_edge(START, "initialize_session")
    builder.add_edge("initialize_session", "analyze_case")
    builder.add_edge("analyze_case", "plan_sides")
    builder.add_edge("plan_sides", "run_opening_phase")
    builder.add_edge("run_opening_phase", "run_witness_loop")
    builder.add_edge("run_witness_loop", "prepare_closing_record")
    builder.add_edge("prepare_closing_record", "run_closing_phase")
    builder.add_edge("run_closing_phase", "run_deliberation")
    builder.add_edge("run_deliberation", "run_evaluation")
    builder.add_edge("run_evaluation", END)
    return builder.compile()


def _require_initialized(
    state: V2AiAiState,
) -> tuple[CompiledCasePackage, TrialRuntimeState]:
    if state.case_package is None or state.runtime is None:
        raise ValueError("V2 session must be initialized")
    return state.case_package, state.runtime


def _first_side(case_package: CompiledCasePackage) -> PartySide:
    return (
        PartySide.PROSECUTION
        if any(party.side == PartySide.PROSECUTION for party in case_package.parties)
        else PartySide.PLAINTIFF
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
