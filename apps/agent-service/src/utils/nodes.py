from __future__ import annotations

from typing import Literal, TypedDict

from . import types
from .helpers import (
    build_witness_queue as build_witness_queue_from_plans,
    get_witness_by_id,
    get_witnesses_by_side,
    log_graph_event,
)
from .prompts import (
    closing_defense_prompt,
    closing_prosecution_prompt,
    defense_strategy_prompt,
    opening_defense_prompt,
    opening_prosecution_prompt,
    prosecution_strategy_prompt,
    summarize_trial_transcript_prompt,
    verdict_prompt,
)
from ..subgraphs.witness.graph import build_witness_graph
from ..subgraphs.witness.state import WitnessExaminationState
from .llm import judge_llm, invoke_structured
from .state import TrialState


class WitnessPlanUpdate(TypedDict):
    prosecution_witness_plan: list[str]
    node_telemetry: list[types.NodeTelemetry]


class DefensePlanUpdate(TypedDict):
    defense_witness_plan: list[str]
    node_telemetry: list[types.NodeTelemetry]


class TranscriptUpdate(TypedDict):
    full_trial_transcript: list[types.TranscriptTurn]
    node_telemetry: list[types.NodeTelemetry]


class WitnessQueueUpdate(TypedDict):
    witness_queue: list[str]
    prosecution_witness_plan: list[str]
    defense_witness_plan: list[str]


class WitnessSelectionUpdate(TypedDict):
    current_witness_id: str | None
    witness_queue: list[str]


class WitnessExaminationUpdate(TypedDict):
    full_trial_transcript: list[types.TranscriptTurn]
    node_telemetry: list[types.NodeTelemetry]


class SummaryUpdate(TypedDict):
    trial_summary: str
    node_telemetry: list[types.NodeTelemetry]


class VerdictUpdate(TypedDict):
    verdict: types.VerdictOutput
    full_trial_transcript: list[types.TranscriptTurn]
    node_telemetry: list[types.NodeTelemetry]


_witness_graph = build_witness_graph()


def load_case_template_node(state: TrialState) -> dict[str, object]:
    log_graph_event("load_case_template", case_id=state.case_file.case_id)
    return {}


def plan_prosecution_strategy_node(state: TrialState) -> WitnessPlanUpdate:
    own_witnesses = get_witnesses_by_side(state.case_file, "prosecution")
    system_prompt, user_prompt = prosecution_strategy_prompt(state, own_witnesses)
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.WitnessPlan,
        node_name="plan_prosecution_strategy",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="planning",
    )
    return {
        "prosecution_witness_plan": result.witness_ids,
        "node_telemetry": telemetry,
    }


def plan_defense_strategy_node(state: TrialState) -> DefensePlanUpdate:
    own_witnesses = get_witnesses_by_side(state.case_file, "defense")
    opposing_public_witnesses = get_witnesses_by_side(state.case_file, "prosecution")
    system_prompt, user_prompt = defense_strategy_prompt(
        state, own_witnesses, opposing_public_witnesses
    )
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.WitnessPlan,
        node_name="plan_defense_strategy",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="planning",
    )
    return {
        "defense_witness_plan": result.witness_ids,
        "node_telemetry": telemetry,
    }


def opening_prosecution_node(state: TrialState) -> TranscriptUpdate:
    system_prompt, user_prompt = opening_prosecution_prompt(state)
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.OpeningStatement,
        node_name="opening_prosecution",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="opening",
    )
    turn = types.TranscriptTurn(
        scene="opening",
        speaker_id="prosecution",
        text=result.statement,
    )
    return {"full_trial_transcript": [turn], "node_telemetry": telemetry}


def opening_defense_node(state: TrialState) -> TranscriptUpdate:
    system_prompt, user_prompt = opening_defense_prompt(state)
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.OpeningStatement,
        node_name="opening_defense",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="opening",
    )
    turn = types.TranscriptTurn(
        scene="opening",
        speaker_id="defense",
        text=result.statement,
    )
    return {"full_trial_transcript": [turn], "node_telemetry": telemetry}


def build_witness_queue_node(state: TrialState) -> WitnessQueueUpdate:
    valid_witness_ids = {witness.witness_id for witness in state.case_file.witnesses}
    prosecution_witness_plan = [
        witness_id
        for witness_id in state.prosecution_witness_plan
        if witness_id in valid_witness_ids
    ]
    defense_witness_plan = [
        witness_id
        for witness_id in state.defense_witness_plan
        if witness_id in valid_witness_ids
    ]
    return {
        "prosecution_witness_plan": prosecution_witness_plan,
        "defense_witness_plan": defense_witness_plan,
        "witness_queue": build_witness_queue_from_plans(
            prosecution_witness_plan,
            defense_witness_plan,
        )
    }


def select_next_witness_node(state: TrialState) -> WitnessSelectionUpdate:
    if not state.witness_queue:
        return {
            "current_witness_id": None,
            "witness_queue": [],
        }

    return {
        "current_witness_id": state.witness_queue[0],
        "witness_queue": state.witness_queue[1:],
    }


def route_after_witness_selection(
    state: TrialState,
) -> Literal["summarize_trial_transcript", "examine_witness"]:
    return (
        "summarize_trial_transcript"
        if state.current_witness_id is None
        else "examine_witness"
    )


def examine_witness_node(state: TrialState) -> WitnessExaminationUpdate:
    if state.current_witness_id is None:
        raise ValueError("current_witness_id must be set before examining a witness")

    witness = get_witness_by_id(state.case_file, state.current_witness_id)
    witness_state = WitnessExaminationState(
        case_file=state.case_file,
        run_id=state.run_id,
        current_witness_id=state.current_witness_id,
        examining_attorney=witness.called_by,
    )
    result = _witness_graph.invoke(witness_state)
    result_state = (
        result
        if isinstance(result, WitnessExaminationState)
        else WitnessExaminationState.model_validate(result)
    )
    return {
        "full_trial_transcript": result_state.current_witness_transcript,
        "node_telemetry": result_state.node_telemetry,
    }


def summarize_trial_transcript_node(state: TrialState) -> SummaryUpdate:
    transcript = "\n".join(
        f"{turn.speaker_id}: {turn.text}" for turn in state.full_trial_transcript
    )
    system_prompt, user_prompt = summarize_trial_transcript_prompt(state, transcript)
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.TrialSummary,
        node_name="summarize_trial_transcript",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="summary",
    )
    return {"trial_summary": result.summary_text, "node_telemetry": telemetry}


def closing_prosecution_node(state: TrialState) -> TranscriptUpdate:
    summary = state.trial_summary or "(no summary available)"
    system_prompt, user_prompt = closing_prosecution_prompt(state, summary)
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.ClosingArgument,
        node_name="closing_prosecution",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="closing",
    )
    turn = types.TranscriptTurn(
        scene="closing",
        speaker_id="prosecution",
        text=result.statement,
    )
    return {"full_trial_transcript": [turn], "node_telemetry": telemetry}


def closing_defense_node(state: TrialState) -> TranscriptUpdate:
    summary = state.trial_summary or "(no summary available)"
    prosecution_closing = state.full_trial_transcript[-1].text
    system_prompt, user_prompt = closing_defense_prompt(
        state, summary, prosecution_closing
    )
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.ClosingArgument,
        node_name="closing_defense",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="closing",
    )
    turn = types.TranscriptTurn(
        scene="closing",
        speaker_id="defense",
        text=result.statement,
    )
    return {"full_trial_transcript": [turn], "node_telemetry": telemetry}


def verdict_node(state: TrialState) -> VerdictUpdate:
    summary = state.trial_summary or "(no summary available)"
    prosecution_closing = (
        state.full_trial_transcript[-2].text
        if len(state.full_trial_transcript) >= 2
        else ""
    )
    defense_closing = (
        state.full_trial_transcript[-1].text if state.full_trial_transcript else ""
    )
    evidence_for_citation = "\n".join(
        f"- {evidence.evidence_id}: {evidence.description}"
        for evidence in state.case_file.evidence
    )
    system_prompt, user_prompt = verdict_prompt(
        state,
        summary,
        prosecution_closing,
        defense_closing,
        chunks_text=evidence_for_citation,
    )
    telemetry: list[types.NodeTelemetry] = []
    result = invoke_structured(
        system_prompt,
        user_prompt,
        types.VerdictOutput,
        llm=judge_llm,
        node_name="verdict",
        telemetry_sink=telemetry.append,
        stage="trial",
        phase="verdict",
    )
    verdict_turn = types.TranscriptTurn(
        scene="verdict",
        speaker_id="judge",
        text=result.reasoning,
        cited_chunk_ids=result.cited_chunk_ids,
    )
    return {
        "verdict": result,
        "full_trial_transcript": [verdict_turn],
        "node_telemetry": telemetry,
    }
