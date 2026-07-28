from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from courtroom_engine.application.examination import (
    WitnessExaminationOutput,
    run_witness_examination,
)
from courtroom_engine.domain.procedure import ExaminationMode
from courtroom_engine.domain.strategy import PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
from pydantic import BaseModel


class WitnessExaminationState(BaseModel):
    case_package: CompiledCasePackage
    runtime: TrialRuntimeState
    strategy: PartyStrategy
    witness_id: str
    mode: ExaminationMode = ExaminationMode.DIRECT
    output: WitnessExaminationOutput | None = None
    status: str = "created"


def run_examination_node(state: WitnessExaminationState) -> WitnessExaminationState:
    return state.model_copy(
        update={
            "output": run_witness_examination(
                case_package=state.case_package,
                state=state.runtime,
                strategy=state.strategy,
                witness_id=state.witness_id,
                mode=state.mode,
            ),
            "status": "witness_examination_complete",
        }
    )


def build_witness_examination_graph():
    builder = StateGraph(WitnessExaminationState)
    builder.add_node("run_structured_examination", run_examination_node)
    builder.add_edge(START, "run_structured_examination")
    builder.add_edge("run_structured_examination", END)
    return builder.compile()
