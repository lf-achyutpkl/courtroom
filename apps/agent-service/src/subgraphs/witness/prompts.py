from ... import TrialState, types
from ...utils.helpers import (
    render_case_context,
    render_witness_private,
    spoken_style_rules,
)


def ask_question_prompt(
    state: TrialState,
    witness_context: str,
    attorney: str,
    phase: str,
    prior_questions_this_phase: int,
    transcript_so_far: str,
) -> tuple[str, str]:
    case_ctx = render_case_context(state.case_file)

    system_prompt = f"""{case_ctx}
      You are {attorney}'s attorney, conducting {phase} examination.
      Witness on the stand: {witness_context}
      Ask exactly one narrow, non-redundant question.
      Prefer 2-4 high-value questions for this phase, then set is_final=true.
      Keep the question concise and grounded in the current witness context.
      The transcript is fed directly to the frontend/TTS system, so include one
      realistic inline delivery tag such as [steady], [sharp], [measured], or
      [pressing] in the question itself."""

    user_prompt = (
        f"Questions asked by {attorney} in this phase so far: {prior_questions_this_phase}\n"
        f"Recent examination transcript:\n{transcript_so_far or '(none yet)'}"
    )
    return system_prompt, user_prompt


def objection_check_prompt(
    state: TrialState, opposing: str, last_question: str | None
) -> tuple[str, str]:
    system_prompt = f"""You are {opposing}'s attorney. Evaluate the question just asked and decide
      whether to object. Objection types: hearsay, leading, relevance, speculation,
      character_evidence, argumentative. Only object when genuinely warranted.
      Return a terse decision."""

    user_prompt = (
        f"Examination phase: {state.examination_phase}\n"
        f"Examining attorney: {state.examining_attorney}\n"
        f"Question just asked: {last_question}"
    )
    return system_prompt, user_prompt


def judge_ruling_prompt(
    state: TrialState,
    objection_type: str | None,
    question: str | None,
    chunks_text: str,
) -> tuple[str, str]:
    system_prompt = f"""You are the presiding judge ruling on a {objection_type} objection.
      Apply ordinary courtroom evidence principles conservatively. If retrieved
      rules/precedent are provided, base your ruling and reasoning on them and cite
      only chunk_ids that appear below. Keep the ruling concise.
      The spoken ruling must include inline delivery tags for TTS/frontend use."""

    user_prompt = (
        f"Examination phase: {state.examination_phase}\n"
        f"Examining attorney: {state.examining_attorney}\n"
        f"Question objected to: {question}\n\n"
        f"Retrieved rules/precedent:\n{chunks_text or '(none retrieved)'}"
    )
    return system_prompt, user_prompt


def witness_answer_prompt(
    state: TrialState,
    witness: types.WitnessProfile,
    question: str | None,
    transcript_so_far: str,
) -> tuple[str, str]:
    case_ctx = render_case_context(state.case_file)
    system_prompt = f"""{case_ctx}
      You ARE the witness: {render_witness_private(witness)}
      Answer only from what you actually know. If asked something outside your
      knowledge, say so honestly rather than inventing details. Stay consistent
      with anything you've already said in this testimony. Keep the answer concise.
      {spoken_style_rules(3, "a witness under oath")}"""

    user_prompt = f"Question: {question}\n\nRecent testimony:\n{transcript_so_far}"
    return system_prompt, user_prompt
