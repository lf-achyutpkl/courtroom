from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from ..utils import types
from ..utils.helpers import get_witnesses_by_side
from ..utils.nodes import (
    build_witness_queue_node,
    closing_defense_node,
    closing_prosecution_node,
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
from ..utils.state import TrialState
from .state import InteractiveTrialState
from .transcription import transcribe_deepgram
from .witness_graph import build_ai_human_witness_graph


def _human_plan(state: TrialState) -> dict[str, object]:
    valid = {
        w.witness_id
        for w in get_witnesses_by_side(state.case_file, state.human_attorney_side)
    }
    plan = state.human_witness_plan
    if len(plan) != len(set(plan)) or any(
        witness_id not in valid for witness_id in plan
    ):
        raise ValueError("human_witness_plan has invalid witness IDs")
    key = f"{state.human_attorney_side}_witness_plan"
    return {key: plan}


def _strategy_prosecution(state: TrialState) -> dict[str, object]:
    return (
        _human_plan(state)
        if state.human_attorney_side == "prosecution"
        else dict(plan_prosecution_strategy_node(state))
    )


def _strategy_defense(state: TrialState) -> dict[str, object]:
    return (
        _human_plan(state)
        if state.human_attorney_side == "defense"
        else dict(plan_defense_strategy_node(state))
    )


def _human_turn(
    state: TrialState,
    scene: Literal["opening", "closing"],
    side: Literal["prosecution", "defense"],
) -> dict[str, object]:
    payload = interrupt(
        {
            "kind": f"human_{scene}",
            "attorney_side": side,
            "required": ["audio_base64", "mime_type"],
        }
    )
    if not isinstance(payload, dict):
        raise ValueError("human voice turn must be resumed with an audio payload")
    text = transcribe_deepgram(payload)
    return {
        "full_trial_transcript": [
            types.TranscriptTurn(scene=scene, speaker_id=side, text=text)
        ]
    }


def _opening_prosecution(state: TrialState) -> dict[str, object]:
    return (
        _human_turn(state, "opening", "prosecution")
        if state.human_attorney_side == "prosecution"
        else dict(opening_prosecution_node(state))
    )


def _opening_defense(state: TrialState) -> dict[str, object]:
    return (
        _human_turn(state, "opening", "defense")
        if state.human_attorney_side == "defense"
        else dict(opening_defense_node(state))
    )


def _closing_prosecution(state: TrialState) -> dict[str, object]:
    return (
        _human_turn(state, "closing", "prosecution")
        if state.human_attorney_side == "prosecution"
        else dict(closing_prosecution_node(state))
    )


def _closing_defense(state: TrialState) -> dict[str, object]:
    return (
        _human_turn(state, "closing", "defense")
        if state.human_attorney_side == "defense"
        else dict(closing_defense_node(state))
    )


def build_ai_human_graph(*, checkpointer: Any | None = None):
    builder = StateGraph(InteractiveTrialState)
    for name, node in (
        ("load_case_template", load_case_template_node),
        ("prosecution_strategy", _strategy_prosecution),
        ("defense_strategy", _strategy_defense),
        ("build_witness_queue", build_witness_queue_node),
        ("opening_prosecution", _opening_prosecution),
        ("opening_defense", _opening_defense),
        ("select_next_witness", select_next_witness_node),
        ("examine_witness", build_ai_human_witness_graph()),
        ("summarize_trial_transcript", summarize_trial_transcript_node),
        ("closing_prosecution", _closing_prosecution),
        ("closing_defense", _closing_defense),
        ("verdict", verdict_node),
    ):
        builder.add_node(name, node)
    builder.add_edge(START, "load_case_template")
    builder.add_edge("load_case_template", "prosecution_strategy")
    builder.add_edge("load_case_template", "defense_strategy")
    builder.add_edge(
        ["prosecution_strategy", "defense_strategy"], "build_witness_queue"
    )
    builder.add_edge("build_witness_queue", "opening_prosecution")
    builder.add_edge("opening_prosecution", "opening_defense")
    builder.add_edge("opening_defense", "select_next_witness")
    builder.add_conditional_edges("select_next_witness", route_after_witness_selection)
    builder.add_edge("examine_witness", "select_next_witness")
    builder.add_edge("summarize_trial_transcript", "closing_prosecution")
    builder.add_edge("closing_prosecution", "closing_defense")
    builder.add_edge("closing_defense", "verdict")
    builder.add_edge("verdict", END)
    return builder.compile(checkpointer=checkpointer)
