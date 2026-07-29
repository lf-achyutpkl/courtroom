from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from courtroom_engine.application.coaching import run_coaching
from courtroom_engine.domain.coaching import CoachingReport
from courtroom_engine.domain.evaluation import EvaluationReport


class CoachingState(BaseModel):
    evaluation: EvaluationReport
    report: CoachingReport | None = None
    status: str = "created"


def run_coaching_node(state: CoachingState) -> CoachingState:
    return state.model_copy(
        update={
            "report": run_coaching(evaluation=state.evaluation),
            "status": "coaching_complete",
        }
    )


def build_coaching_graph():
    builder = StateGraph(CoachingState)
    builder.add_node("run_grounded_coaching", run_coaching_node)
    builder.add_edge(START, "run_grounded_coaching")
    builder.add_edge("run_grounded_coaching", END)
    return builder.compile()
