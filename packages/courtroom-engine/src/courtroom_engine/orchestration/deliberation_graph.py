from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from courtroom_engine.application.deliberation import run_judicial_deliberation
from courtroom_engine.domain.deliberation import DeliberationReport
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState


class DeliberationState(BaseModel):
    case_package: CompiledCasePackage
    runtime: TrialRuntimeState
    report: DeliberationReport | None = None
    status: str = "created"


def run_deliberation_node(state: DeliberationState) -> DeliberationState:
    return state.model_copy(
        update={
            "report": run_judicial_deliberation(
                case_package=state.case_package,
                state=state.runtime,
            ),
            "status": "deliberation_complete",
        }
    )


def build_judicial_deliberation_graph():
    builder = StateGraph(DeliberationState)
    builder.add_node("run_structured_deliberation", run_deliberation_node)
    builder.add_edge(START, "run_structured_deliberation")
    builder.add_edge("run_structured_deliberation", END)
    return builder.compile()
