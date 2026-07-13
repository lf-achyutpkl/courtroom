from ... import types, TrialState


def render_witness_public(witness: types.WitnessProfile) -> str:
    return (
        f"- {witness.witness_id} ({witness.name}, called by {witness.called_by}): "
        f"{witness.persona}"
    )


def render_witness_private(witness: types.WitnessProfile) -> str:
    return (
        f"{render_witness_public(witness)}\n"
        f"  Known facts (only you/your side sees this): {witness.knowledge_scope}"
    )


def _preview_text(text: str | None, limit: int = 220) -> str:
    if not text:
        return "-"
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def format_recent_testimony(
    turns: list[types.TranscriptTurn], max_turns: int = 6
) -> str:
    testimony_turns = [turn for turn in turns if turn.scene in {"direct", "cross"}]
    recent_turns = testimony_turns[-max_turns:]
    return "\n".join(
        f"[{turn.scene}] {turn.speaker_id}: {_preview_text(turn.text)}"
        for turn in recent_turns
    )


def append_witness_turn(
    state: TrialState, turn: types.TranscriptTurn
) -> list[types.TranscriptTurn]:
    return state.current_witness_transcript + [turn]


def current_phase_question_count(state: TrialState) -> int:
    return sum(
        1
        for turn in state.current_witness_transcript
        if turn.scene == state.examination_phase
        and turn.speaker_id == state.examining_attorney
    )


def should_end_phase(state: TrialState) -> bool:
    return (
        state.attorney_is_done or current_phase_question_count(state) >= state.max_turns
    )


def phase_complete_next_node(state: TrialState):
    return "swap_to_cross" if state.examination_phase == "direct" else "__end__"
