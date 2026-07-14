from __future__ import annotations

from textwrap import dedent

from .helpers import (
    render_case_context,
    render_witness_private,
    render_witness_public,
    spoken_style_rules,
)
from .state import TrialState
from .types import WitnessProfile


def _clean_block(text: str) -> str:
    return dedent(text).strip()


def _format_section(title: str, body: str | None) -> str:
    cleaned = _clean_block(body or "")
    if not cleaned:
        return ""
    return f"{title}\n{cleaned}"


def _format_list(items: list[str], empty_text: str = "(none)") -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def build_system_prompt(
    *,
    role_instruction: str,
    task_instructions: list[str],
    case_context: str | None = None,
    style_rules: str | None = None,
) -> str:
    task_body = _format_list(task_instructions)
    return "\n\n".join(
        section
        for section in (
            _format_section("CASE CONTEXT", case_context),
            _format_section("ROLE", role_instruction),
            _format_section("TASK", task_body),
            _format_section("STYLE", style_rules),
        )
        if section
    )


def build_user_prompt(*sections: tuple[str, str | None]) -> str:
    return "\n\n".join(
        section
        for section in (
            _format_section(title, body) for title, body in sections if body is not None
        )
        if section
    )


def prosecution_strategy_prompt(
    state: TrialState, own_witnesses: list[WitnessProfile]
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_with_evidence"),
        role_instruction="""
        You are the prosecution's lead attorney planning trial strategy.
        """,
        task_instructions=[
            "Choose which of your witnesses to call and in what order.",
            "Use only your side's private witness details.",
            "Optimize for proving the charge or claim efficiently.",
        ],
    )
    user_prompt = build_user_prompt(
        (
            "YOUR AVAILABLE WITNESSES",
            "\n".join(render_witness_private(witness) for witness in own_witnesses)
            or "(none)",
        ),
    )
    return system_prompt, user_prompt


def defense_strategy_prompt(
    state: TrialState,
    own_witnesses: list[WitnessProfile],
    opposing_public_witnesses: list[WitnessProfile],
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_with_evidence"),
        role_instruction="""
        You are the defense's lead attorney planning trial strategy.
        """,
        task_instructions=[
            "Work independently from the prosecution and assume you do not know their final plan.",
            "Choose which of your own witnesses to call, if any, and in what order.",
            "Calling zero witnesses is a valid strategic choice.",
        ],
    )
    user_prompt = build_user_prompt(
        (
            "YOUR AVAILABLE WITNESSES",
            "\n".join(render_witness_private(witness) for witness in own_witnesses)
            or "(none)",
        ),
        (
            "PROSECUTION WITNESSES ON RECORD",
            "\n".join(
                render_witness_public(witness)
                for witness in opposing_public_witnesses
            )
            or "(none)",
        ),
    )
    return system_prompt, user_prompt


def opening_prosecution_prompt(state: TrialState) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_core"),
        role_instruction="""
        You are the prosecution delivering an opening statement.
        """,
        task_instructions=[
            "Preview what the evidence will show.",
            "Do not argue the case or mention facts not expected to come in at trial.",
        ],
        style_rules=spoken_style_rules(4, "a prosecutor addressing the jury"),
    )
    user_prompt = build_user_prompt(
        ("PLANNED WITNESS ORDER", str(state.prosecution_witness_plan)),
    )
    return system_prompt, user_prompt


def opening_defense_prompt(state: TrialState) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_core"),
        role_instruction="""
        You are the defense delivering an opening statement.
        """,
        task_instructions=[
            "Respond to the prosecution's framing if it helps your theory of the case.",
            "Preview your expected evidence without arguing unsupported facts.",
        ],
        style_rules=spoken_style_rules(4, "a defense attorney addressing the jury"),
    )
    prosecution_opening = state.full_trial_transcript[-1].text
    user_prompt = build_user_prompt(
        ("PROSECUTION OPENING", prosecution_opening),
        ("PLANNED WITNESS ORDER", str(state.defense_witness_plan)),
    )
    return system_prompt, user_prompt


def summarize_trial_transcript_prompt(
    state: TrialState, transcript: str
) -> tuple[str, str]:
    del state
    system_prompt = build_system_prompt(
        role_instruction="""
        You are a neutral court clerk preparing a concise trial summary.
        """,
        task_instructions=[
            "Summarize only what is in the trial record.",
            "Capture openings, material testimony, notable rulings, evidentiary conflicts, and the strongest points for both sides.",
            "Do not invent facts or import off-record knowledge.",
        ],
    )
    user_prompt = build_user_prompt(
        ("FULL TRIAL TRANSCRIPT", transcript),
    )
    return system_prompt, user_prompt


def closing_prosecution_prompt(state: TrialState, summary: str) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_header"),
        role_instruction="""
        You are the prosecution delivering a closing argument.
        """,
        task_instructions=[
            "Argue only from what was actually presented at trial.",
            "Do not introduce new evidence.",
        ],
        style_rules=spoken_style_rules(5, "a prosecutor delivering closing"),
    )
    user_prompt = build_user_prompt(
        ("TRIAL SUMMARY", summary),
    )
    return system_prompt, user_prompt


def closing_defense_prompt(
    state: TrialState, summary: str, prosecution_closing: str
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_header"),
        role_instruction="""
        You are the defense delivering a closing argument.
        """,
        task_instructions=[
            "Argue only from what was actually presented at trial.",
            "Do not introduce new evidence.",
            "You may respond directly to the prosecution's closing.",
        ],
        style_rules=spoken_style_rules(5, "a defense attorney delivering closing"),
    )
    user_prompt = build_user_prompt(
        ("TRIAL SUMMARY", summary),
        ("PROSECUTION CLOSING", prosecution_closing),
    )
    return system_prompt, user_prompt


def verdict_prompt(
    state: TrialState,
    summary: str,
    chunks_text: str,
) -> tuple[str, str]:
    system_prompt = build_system_prompt(
        case_context=render_case_context(state.case_file, profile="case_header"),
        role_instruction="""
        You are the presiding judge rendering a verdict.
        """,
        task_instructions=[
            "Base the decision only on what was presented at trial and any retrieved rules or precedent.",
            "Do not rely on material outside the record.",
            "Cite only chunk_ids that appear in the retrieved rules or precedent section when citing authority.",
        ],
        style_rules=spoken_style_rules(4, "a judge delivering a verdict from the bench"),
    )
    user_prompt = build_user_prompt(
        ("TRIAL SUMMARY", summary),
        ("RETRIEVED RULES/PRECEDENT", chunks_text or "(none retrieved)"),
    )
    return system_prompt, user_prompt
