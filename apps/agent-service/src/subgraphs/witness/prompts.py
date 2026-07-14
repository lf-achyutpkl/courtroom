from ... import types
from ...utils.helpers import (
    render_case_context,
    render_witness_private,
    spoken_style_rules,
)
from ...utils.prompts import build_system_prompt, build_user_prompt
from .state import WitnessExaminationState


def ask_question_prompt(
    state: WitnessExaminationState,
    witness_context: str,
    attorney: str,
    phase: str,
    prior_questions_this_phase: int,
    transcript_so_far: str,
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="facts_and_evidence"),
        role_instruction="""
        You are a trial attorney examining a witness.
        """,
        task_instructions=[
            "Ask exactly one narrow, non-redundant question.",
            "Prefer 2-4 high-value questions for the phase, then set is_final=true.",
            "Keep the question concise and grounded in the witness context and prior testimony.",
            "Include one realistic inline delivery tag such as [steady], [sharp], [measured], or [pressing] in the question itself.",
        ],
    )

    user_prompt = build_user_prompt(
        ("EXAMINING ATTORNEY", attorney),
        ("EXAMINATION PHASE", phase),
        ("WITNESS ON THE STAND", witness_context),
        (
            "QUESTIONS ASKED SO FAR THIS PHASE",
            str(prior_questions_this_phase),
        ),
        ("RECENT EXAMINATION TRANSCRIPT", transcript_so_far or "(none yet)"),
    )
    return system_prompt, user_prompt


def objection_check_prompt(
    state: WitnessExaminationState, opposing: str, last_question: str | None
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        role_instruction="""
        You are the non-examining attorney deciding whether to object.
        """,
        task_instructions=[
            "Object only when the question genuinely warrants it.",
            "Available objection types are hearsay, leading, relevance, speculation, character_evidence, and argumentative.",
            "Return a terse decision.",
        ],
    )

    user_prompt = build_user_prompt(
        ("OBJECTING ATTORNEY", opposing),
        ("EXAMINATION PHASE", state.examination_phase),
        ("EXAMINING ATTORNEY", state.examining_attorney),
        ("QUESTION JUST ASKED", last_question or "(none)"),
    )
    return system_prompt, user_prompt


def judge_ruling_prompt(
    state: WitnessExaminationState,
    objection_type: str | None,
    question: str | None,
    chunks_text: str,
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        role_instruction="""
        You are the presiding judge ruling on an objection.
        """,
        task_instructions=[
            "Apply ordinary courtroom evidence principles conservatively.",
            "If retrieved rules or precedent are provided, base the ruling and reasoning on them.",
            "Cite only chunk_ids that appear in the retrieved rules or precedent section.",
            "Keep the ruling concise and include inline delivery tags for frontend and TTS use.",
        ],
    )

    user_prompt = build_user_prompt(
        ("EXAMINATION PHASE", state.examination_phase),
        ("EXAMINING ATTORNEY", state.examining_attorney),
        ("OBJECTION TYPE", objection_type or "(unspecified)"),
        ("QUESTION OBJECTED TO", question or "(none)"),
        ("RETRIEVED RULES/PRECEDENT", chunks_text or "(none retrieved)"),
    )
    return system_prompt, user_prompt


def witness_answer_prompt(
    state: WitnessExaminationState,
    witness: types.WitnessProfile,
    question: str | None,
    transcript_so_far: str,
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="disputed_facts_only"),
        role_instruction="""
        You are a witness under oath answering questions.
        """,
        task_instructions=[
            "Answer only from what you actually know.",
            "If asked something outside your knowledge, say so honestly instead of inventing details.",
            "Stay consistent with anything already said in this testimony.",
            "Keep the answer concise.",
        ],
        style_rules=spoken_style_rules(3, "a witness under oath"),
    )

    user_prompt = build_user_prompt(
        ("WITNESS PROFILE", render_witness_private(witness)),
        ("QUESTION", question or "(none)"),
        ("RECENT TESTIMONY", transcript_so_far or "(none yet)"),
    )
    return system_prompt, user_prompt
