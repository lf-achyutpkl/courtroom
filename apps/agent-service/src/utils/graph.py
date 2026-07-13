from langgraph.graph import END, START, StateGraph

from .nodes import (
    build_witness_queue_node,
    closing_defense_node,
    closing_prosecution_node,
    examine_witness_node,
    load_case_template_node,
    opening_defense_node,
    opening_prosecution_node,
    plan_defense_strategy_node,
    plan_prosecution_strategy_node,
    route_after_witness_selection,
    select_next_witness_node,
    summarize_trial_transcript_node,
    verdict_node,
)
from .state import TrialState


def build_graph():
    builder = StateGraph(TrialState)
    builder.add_node("load_case_template", load_case_template_node)
    builder.add_node("prosecution_strategy", plan_prosecution_strategy_node)
    builder.add_node("defense_strategy", plan_defense_strategy_node)
    builder.add_node("build_witness_queue", build_witness_queue_node)
    builder.add_node("opening_prosecution", opening_prosecution_node)
    builder.add_node("opening_defense", opening_defense_node)
    builder.add_node("select_next_witness", select_next_witness_node)
    builder.add_node("examine_witness", examine_witness_node)
    builder.add_node("summarize_trial_transcript", summarize_trial_transcript_node)
    builder.add_node("closing_prosecution", closing_prosecution_node)
    builder.add_node("closing_defense", closing_defense_node)
    builder.add_node("verdict", verdict_node)

    builder.add_edge(START, "load_case_template")
    builder.add_edge("load_case_template", "prosecution_strategy")
    builder.add_edge("load_case_template", "defense_strategy")
    builder.add_edge(
        ["prosecution_strategy", "defense_strategy"],
        "build_witness_queue",
    )
    builder.add_edge("build_witness_queue", "opening_prosecution")
    builder.add_edge("opening_prosecution", "opening_defense")
    builder.add_edge("opening_defense", "select_next_witness")
    builder.add_conditional_edges(
        "select_next_witness",
        route_after_witness_selection,
    )
    builder.add_edge("examine_witness", "select_next_witness")
    builder.add_edge("summarize_trial_transcript", "closing_prosecution")
    builder.add_edge("closing_prosecution", "closing_defense")
    builder.add_edge("closing_defense", "verdict")
    builder.add_edge("verdict", END)

    return builder.compile()
