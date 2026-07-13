from ... import types
from ...utils.config import TRIAL_CONFIG
from ...utils.helpers import format_recent_transcript
from .state import WitnessExaminationState


def format_recent_testimony(
    turns: list[types.TranscriptTurn],
    max_turns: int = TRIAL_CONFIG.context_window_turns,
) -> str:
    return format_recent_transcript(
        turns,
        max_turns=max_turns,
        scenes={"direct", "cross"},
        include_scene=True,
    )


def append_witness_turn(
    state: WitnessExaminationState, turn: types.TranscriptTurn
) -> list[types.TranscriptTurn]:
    return state.current_witness_transcript + [turn]


def current_phase_question_count(state: WitnessExaminationState) -> int:
    return sum(
        1
        for turn in state.current_witness_transcript
        if turn.scene == state.examination_phase
        and turn.speaker_id == state.examining_attorney
    )


def should_end_phase(state: WitnessExaminationState) -> bool:
    return (
        state.attorney_is_done
        or current_phase_question_count(state) >= TRIAL_CONFIG.max_questions_per_phase
    )


def phase_complete_next_node(state: WitnessExaminationState):
    return "swap_to_cross" if state.examination_phase == "direct" else "__end__"
