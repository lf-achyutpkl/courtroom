from typing import Literal

from ...utils.config import TRIAL_CONFIG
from ...utils.helpers import (
    get_witness_by_id,
    render_witness_private,
    render_witness_public,
)
from .helpers import (
    format_recent_testimony,
    append_witness_turn,
    current_phase_question_count,
    should_end_phase,
    phase_complete_next_node,
)
from .prompts import (
    ask_question_prompt,
    objection_check_prompt,
    judge_ruling_prompt,
    witness_answer_prompt,
)
from ... import invoke, llm, types
from .state import WitnessExaminationState


def ask_question_node(state: WitnessExaminationState) -> dict:
    """Ask a question based on the current trial state."""
    if state.current_witness_id is None:
        raise ValueError("current_witness_id must be set before asking a question")

    witness = get_witness_by_id(state.case_file, state.current_witness_id)
    attorney, phase = state.examining_attorney, state.examination_phase
    knows_private = phase == "direct" and witness.called_by == attorney
    witness_context = (
        render_witness_private(witness)
        if knows_private
        else render_witness_public(witness)
    )
    prior_questions_this_phase = sum(
        1
        for turn in state.current_witness_transcript
        if turn.scene == phase and turn.speaker_id == attorney
    )
    transcript_so_far = format_recent_testimony(
        state.current_witness_transcript, TRIAL_CONFIG.context_window_turns
    )
    system_prompt, user_prompt = ask_question_prompt(
        state,
        witness_context,
        attorney,
        phase,
        prior_questions_this_phase,
        transcript_so_far,
    )

    result: types.ExaminationQuestion = invoke(
        system_prompt,
        user_prompt,
        types.ExaminationQuestion,
        node_name="ask_question",
    )

    turn = types.TranscriptTurn(
        scene=phase,
        speaker_id=attorney,
        text=result.question_text,
    )

    return {
        "current_witness_transcript": append_witness_turn(state, turn),
        "turn_count": current_phase_question_count(state) + 1,
        "attorney_is_done": result.is_final,
        "active_question_text": result.question_text,
    }


def objection_check_node(state: WitnessExaminationState) -> dict:
    opposing = "defense" if state.examining_attorney == "prosecution" else "prosecution"
    last_question = state.active_question_text
    if TRIAL_CONFIG.skip_direct_objections and state.examination_phase == "direct":
        return {"objection_pending": False, "last_objection_type": None}
    system_prompt, user_prompt = objection_check_prompt(state, opposing, last_question)

    result: types.ObjectionDecision = invoke(
        system_prompt,
        user_prompt,
        types.ObjectionDecision,
        node_name="objection_check",
    )

    return {
        "objection_pending": result.objection,
        "last_objection_type": result.objection_type,
    }


def judge_ruling_node(state: WitnessExaminationState) -> dict:
    question = state.active_question_text
    objection_type = state.last_objection_type
    chunks_text = ""
    system_prompt, user_prompt = judge_ruling_prompt(
        state, objection_type, question, chunks_text
    )

    result: types.RulingOutput = invoke(
        system_prompt,
        user_prompt,
        types.RulingOutput,
        llm=llm.judge_llm,
        node_name="judge_ruling",
    )

    turn = types.TranscriptTurn(
        scene="ruling",
        speaker_id="judge",
        text=result.reasoning,
        ruling=result.decision,
        cited_chunk_ids=result.cited_chunk_ids,
    )
    return {
        "last_ruling": result,
        "objection_pending": False,
        "current_witness_transcript": append_witness_turn(state, turn),
    }


def witness_answer_node(state: WitnessExaminationState) -> dict:
    if state.current_witness_id is None:
        raise ValueError("current_witness_id must be set before answering a question")

    witness = get_witness_by_id(state.case_file, state.current_witness_id)
    question = state.active_question_text
    transcript_so_far = format_recent_testimony(
        state.current_witness_transcript, TRIAL_CONFIG.context_window_turns
    )
    system_prompt, user_prompt = witness_answer_prompt(
        state, witness, question, transcript_so_far
    )

    result: types.WitnessAnswer = invoke(
        system_prompt,
        user_prompt,
        types.WitnessAnswer,
        node_name="witness_answer",
    )

    turn = types.TranscriptTurn(
        scene=state.examination_phase,
        speaker_id=witness.witness_id,
        text=result.answer_text,
    )
    return {
        "current_witness_transcript": append_witness_turn(state, turn),
        "active_question_text": None,
    }


def swap_to_cross_node(state: WitnessExaminationState) -> dict:
    if state.current_witness_id is None:
        raise ValueError("current_witness_id must be set before cross examination")

    witness = get_witness_by_id(state.case_file, state.current_witness_id)
    other_side = "defense" if witness.called_by == "prosecution" else "prosecution"

    return {
        "examination_phase": "cross",
        "examining_attorney": other_side,
        "turn_count": 0,
        "attorney_is_done": False,
        "objection_pending": False,
        "last_objection_type": None,
        "last_ruling": None,
        "active_question_text": None,
    }


def route_after_answer(state: WitnessExaminationState):
    if should_end_phase(state):
        next_node = phase_complete_next_node(state)
        return next_node

    return "ask_question"


def route_after_objection_check(
    state: WitnessExaminationState,
) -> Literal["judge_ruling", "witness_answer"]:
    return "judge_ruling" if state.objection_pending else "witness_answer"


def route_after_ruling(state: WitnessExaminationState):
    if state.last_ruling.decision != "sustained":
        next_node = "witness_answer"
    elif should_end_phase(state):
        next_node = phase_complete_next_node(state)
    else:
        next_node = "ask_question"

    return next_node
