from __future__ import annotations

from .helpers import (
    render_case_context,
    render_witness_private,
    render_witness_public,
    spoken_style_rules,
)
from .state import TrialState
from .types import WitnessProfile


def prosecution_strategy_prompt(
    state: TrialState, own_witnesses: list[WitnessProfile]
) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = f"""{case_context}

You are the prosecution's lead attorney planning trial strategy. You see full
details on your own witnesses only. Decide which of your witnesses to call,
and in what order, to best prove the elements of the charge."""
    user_prompt = "Your available witnesses:\n" + "\n".join(
        render_witness_private(witness) for witness in own_witnesses
    )
    return system_prompt, user_prompt


def defense_strategy_prompt(
    state: TrialState,
    own_witnesses: list[WitnessProfile],
    opposing_public_witnesses: list[WitnessProfile],
) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = f"""{case_context}

You are the defense's lead attorney planning trial strategy, working
independently and in parallel with the prosecution — you do not know their
final plan. Decide which of your own witnesses to call, if any, and in what
order. Calling zero witnesses is a valid strategic choice."""
    user_prompt = (
        "Your available witnesses:\n"
        + "\n".join(render_witness_private(witness) for witness in own_witnesses)
        + "\n\nProsecution's witnesses on record (public knowledge only):\n"
        + "\n".join(
            render_witness_public(witness)
            for witness in opposing_public_witnesses
        )
    )
    return system_prompt, user_prompt


def opening_prosecution_prompt(state: TrialState) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = (
        f"{case_context}\n\nYou are the prosecution. Deliver your opening statement "
        "with no argument, only a preview of what the evidence will show. "
        f"{spoken_style_rules(4, 'a prosecutor addressing the jury')}"
    )
    user_prompt = f"Your planned witness order: {state.prosecution_witness_plan}"
    return system_prompt, user_prompt


def opening_defense_prompt(state: TrialState) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = (
        f"{case_context}\n\nYou are the defense. Deliver your opening statement, "
        "responding to the framing prosecution just set up if useful. "
        f"{spoken_style_rules(4, 'a defense attorney addressing the jury')}"
    )
    prosecution_opening = state.full_trial_transcript[-1].text
    user_prompt = (
        f"Prosecution's opening:\n{prosecution_opening}\n\n"
        f"Your planned witness order: {state.defense_witness_plan}"
    )
    return system_prompt, user_prompt


def summarize_trial_transcript_prompt(
    state: TrialState, transcript: str
) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = f"""{case_context}
You are a neutral court clerk preparing a concise trial summary for later
argument and verdict drafting. Summarize only what is in the trial record.
Capture openings, material testimony, notable rulings, conflicts in the
evidence, and the strongest points for both sides. Do not invent facts."""
    user_prompt = f"Full trial transcript so far:\n{transcript}"
    return system_prompt, user_prompt


def closing_prosecution_prompt(state: TrialState, summary: str) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = (
        f"{case_context}\n\nYou are the prosecution. Deliver a closing argument "
        "based only on what was actually presented at trial with no new evidence. "
        f"{spoken_style_rules(5, 'a prosecutor delivering closing')}"
    )
    user_prompt = f"Trial summary:\n{summary}"
    return system_prompt, user_prompt


def closing_defense_prompt(
    state: TrialState, summary: str, prosecution_closing: str
) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = f"""{case_context}
You are the defense. Deliver a closing argument based only on what was
actually presented at trial with no new evidence. You may respond to the
prosecution's closing argument below.
{spoken_style_rules(5, 'a defense attorney delivering closing')}"""
    user_prompt = (
        f"Trial summary:\n{summary}\n\n"
        f"Prosecution's closing argument:\n{prosecution_closing}"
    )
    return system_prompt, user_prompt


def verdict_prompt(
    state: TrialState,
    summary: str,
    prosecution_closing: str,
    defense_closing: str,
    chunks_text: str,
) -> tuple[str, str]:
    case_context = render_case_context(state.case_file)
    system_prompt = f"""{case_context}
You are the presiding judge rendering a verdict. Base your decision only on
what was presented at trial and the evidence listed below.
Your structured cited_chunk_ids must include the decisive evidence IDs from the
case file that support the verdict. Do not cite IDs that are not listed. In the
spoken reasoning, explicitly name the decisive facts tied to those evidence IDs.
{spoken_style_rules(4, 'a judge delivering a verdict from the bench')}"""
    user_prompt = (
        f"Trial summary:\n{summary}\n\n"
        f"Prosecution closing:\n{prosecution_closing}\n\n"
        f"Defense closing:\n{defense_closing}\n\n"
        f"Evidence available for verdict citations:\n{chunks_text or '(none listed)'}"
    )
    return system_prompt, user_prompt
