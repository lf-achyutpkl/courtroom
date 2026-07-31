from __future__ import annotations

from courtroom_engine.application.evaluation import run_evaluation
from courtroom_engine.application.examination import WitnessExaminationOutput
from courtroom_engine.domain.deliberation import DeliberationReport
from courtroom_engine.domain.evaluation import EvaluationReport
from courtroom_engine.domain.strategy import PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


class EvaluationState(BaseModel):
    case_package: CompiledCasePackage
    runtime: TrialRuntimeState
    strategies: tuple[PartyStrategy, ...]
    witness_examinations: tuple[WitnessExaminationOutput, ...]
    deliberation: DeliberationReport
    report: EvaluationReport | None = None
    status: str = "created"


def run_evaluation_node(state: EvaluationState) -> EvaluationState:
    return state.model_copy(
        update={
            "report": run_evaluation(
                case_package=state.case_package,
                state=state.runtime,
                strategies=state.strategies,
                witness_examinations=state.witness_examinations,
                deliberation=state.deliberation,
            ),
            "status": "evaluation_complete",
        }
    )


def build_evaluation_graph():
    builder = StateGraph(EvaluationState)
    builder.add_node("run_structured_evaluation", run_evaluation_node)
    builder.add_edge(START, "run_structured_evaluation")
    builder.add_edge("run_structured_evaluation", END)
    return builder.compile()
