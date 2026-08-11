"""Checkpointed witness examination subgraph for AI-vs-human trials only."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, StateGraph

from ..subgraphs.witness.nodes import (
    ask_question_node,
    judge_ruling_node,
    objection_check_node,
    route_after_answer,
    route_after_objection_check,
    route_after_ruling,
    swap_to_cross_node,
    witness_answer_node,
)
from ..utils.helpers import get_witness_by_id
from .state import InteractiveTrialState


def _initialise_witness(state: InteractiveTrialState) -> dict[str, object]:
    if state.current_witness_id is None:
        raise ValueError("current_witness_id must be set before examining a witness")

    witness = get_witness_by_id(state.case_file, state.current_witness_id)
    return {
        "examining_attorney": witness.called_by,
        "examination_phase": "direct",
        "turn_count": 0,
        "current_witness_transcript": [],
        "objection_pending": False,
        "last_objection_type": None,
        "last_objection_text": None,
        "last_ruling": None,
        "active_question_text": None,
        "attorney_is_done": False,
    }


def _publish_new_turns(node: Any) -> Any:
    """Mirror only a node's newly-produced witness turns into the trial record."""

    def wrapped(state: InteractiveTrialState) -> dict[str, object]:
        update = node(state)
        witness_transcript = update.get("current_witness_transcript")
        if not isinstance(witness_transcript, list):
            return update

        new_turns = witness_transcript[len(state.current_witness_transcript) :]
        if not new_turns:
            return update

        return {**update, "full_trial_transcript": new_turns}

    return wrapped


def _route_after_answer(state: InteractiveTrialState) -> str:
    return route_after_answer(state)


def _route_after_ruling(state: InteractiveTrialState) -> str:
    return route_after_ruling(state)


def build_ai_human_witness_graph(*, checkpointer: Any | None = None):
    """Build a child graph whose interrupt state is saved with its parent.

    It deliberately compiles independently from the AI-vs-AI witness graph,
    but shares the established examination node behavior.  Adding the compiled
    graph as a parent node lets LangGraph persist the child task between a
    question and a later objection response.
    """

    builder = StateGraph(InteractiveTrialState)
    builder.add_node("initialise_witness", _initialise_witness)
    builder.add_node("ask_question", _publish_new_turns(ask_question_node))
    builder.add_node("objection_check", _publish_new_turns(objection_check_node))
    builder.add_node("judge_ruling", _publish_new_turns(judge_ruling_node))
    builder.add_node("witness_answer", _publish_new_turns(witness_answer_node))
    builder.add_node("swap_to_cross", swap_to_cross_node)

    builder.add_edge(START, "initialise_witness")
    builder.add_edge("initialise_witness", "ask_question")
    builder.add_edge("ask_question", "objection_check")
    builder.add_conditional_edges("objection_check", route_after_objection_check)
    builder.add_conditional_edges("judge_ruling", _route_after_ruling)
    builder.add_conditional_edges("witness_answer", _route_after_answer)
    builder.add_edge("swap_to_cross", "ask_question")
    return builder.compile(checkpointer=checkpointer)


_compiled_witness_graph = build_ai_human_witness_graph()


def examine_witness_node(
    state: InteractiveTrialState, config: RunnableConfig
) -> dict[str, object]:
    """Run the witness subgraph and report only the turns/telemetry it added.

    ``InteractiveTrialState`` shares ``full_trial_transcript`` and
    ``node_telemetry`` with the parent trial graph, and both fields use an
    ``add`` reducer. If the compiled subgraph were added directly as a parent
    node (as it shares the same schema), LangGraph would hand the parent the
    subgraph's *entire* final state for those keys -- which already contains
    everything the parent passed in -- and the parent's own reducer would
    append that on top of what it already has, duplicating every prior turn
    and telemetry entry on each witness examination. Invoking the subgraph
    here and returning only the slice produced during this call avoids that.
    Passing `config` through keeps this call nested under the parent's
    checkpoint namespace, so interrupts/resumes for human turns still work.
    """

    transcript_before = len(state.full_trial_transcript)
    telemetry_before = len(state.node_telemetry)

    result = _compiled_witness_graph.invoke(state, config)
    result_state = (
        result
        if isinstance(result, InteractiveTrialState)
        else InteractiveTrialState.model_validate(result)
    )

    return {
        "full_trial_transcript": result_state.full_trial_transcript[
            transcript_before:
        ],
        "node_telemetry": result_state.node_telemetry[telemetry_before:],
    }
