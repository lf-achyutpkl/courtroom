from langgraph.graph import START, StateGraph

from .nodes import (
    ask_question_node,
    swap_to_cross_node,
    witness_answer_node,
    judge_ruling_node,
    objection_check_node,
    route_after_objection_check,
    route_after_ruling,
    route_after_answer,
)
from .state import WitnessExaminationState


def build_witness_graph():
    builder = StateGraph(WitnessExaminationState)
    builder.add_node("ask_question", ask_question_node)
    builder.add_node("objection_check", objection_check_node)
    builder.add_node("judge_ruling", judge_ruling_node)
    builder.add_node("witness_answer", witness_answer_node)
    builder.add_node("swap_to_cross", swap_to_cross_node)

    builder.add_edge(START, "ask_question")
    builder.add_edge("ask_question", "objection_check")
    builder.add_conditional_edges("objection_check", route_after_objection_check)
    builder.add_conditional_edges("judge_ruling", route_after_ruling)
    builder.add_conditional_edges("witness_answer", route_after_answer)
    builder.add_edge("swap_to_cross", "ask_question")
    return builder.compile()
